import ckan.plugins.toolkit as toolkit
from ckanext.tracker.classes import PackageResourceTrackerPlugin
from ckanext.tracker.classes.helpers import link_is_enabled
from worker.geoserver import GeoServerWorkerWrapper
from worker.geoserver.rest import GeoServerRestApi
from worker.geoserver.rest.model import Workspace, DataStore
from helpers import should_publish_to_geoserver, should_unpublish_to_geoserver
import ckan.plugins as plugins
import logic.action.update as action_update
import logic.auth.update as auth_update
from ckanext.tracker_ogr.interface import ITrackerOgr

import logging

logging.basicConfig()
log = logging.getLogger(__name__)


class GeoserverTrackerPlugin(PackageResourceTrackerPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(ITrackerOgr)

    queue_name = 'geoserver'
    worker = GeoServerWorkerWrapper()
    geoserver_link_field_name = 'geoserver_link_enabled'
    api = None
    workspace = None
    data_store = None

    include_resource_fields = ["id", "name", "description"]

    # IConfigurable
    def configure(self, config):
        super(GeoserverTrackerPlugin, self).configure(config)
        geoserver_url = toolkit.config.get('ckanext.{}.geoserver.url'.format(self.name), None)
        configuration = self.get_configuration()
        if geoserver_url is not None:
            self.api = GeoServerRestApi(configuration)
            self.workspace = Workspace(name=configuration.workspace_name)
            self.data_store = DataStore(name=configuration.data_store_name)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')

    # IActions
    def get_actions(self):
        return {
            'geoserver_callback_hook': action_update.geoserver_callback_hook
        }

    # IAuthFunctions
    def get_auth_functions(self):
        return {
            'geoserver_callback_hook': auth_update.geoserver_callback_hook
        }

    # ITrackerOgr
    def callback(self, context, state, resource_dict, dataset_dict):
        '''
        This method is called when the OGR finishes it's task, with one of multiple results (complete, delete etc...)
        If sucessfull - must create/update the geoserver layer
        If deleted - remove layer
        other... we'll see
        '''
        """
        Does not represent the cases where the creation of a resource is preceded by an already existing datastore table
        and in those cases the link should be checked
        """
        # TODO Digest callback value and implement each alternative
        # TODO Call do_resource_update or do_resource_delete or do nothing
        command = None
        geoserver_link_enabled = link_is_enabled(dataset_dict, 'geoserver_link_enabled')
        geoserver_layer_exists = resource_dict.get('format', None) not in ['wms', 'wfs'] and \
            resource_dict.get("wfs_url", None) and resource_dict.get("wms_url", None)
        geoserver_fields = ['name', 'description', 'layer_extent', 'layer_srid']
        geoserver_valid_resource = all([resource_dict.get(field, None) for field in geoserver_fields])
        log.debug("state = {} link_enabled = {} layer_exists = {} valid_resource = {}".format(
            state, geoserver_link_enabled, geoserver_layer_exists, geoserver_valid_resource
        ))
        if geoserver_link_enabled:
            if state == 'created':
                if geoserver_valid_resource:
                    command = self.get_worker().create_datasource
            elif state == 'updated':
                if geoserver_valid_resource:
                    command = self.get_worker().create_datasource
                elif geoserver_layer_exists:
                    command = self.get_worker().delete_datasource
            elif state == 'deleted':
                if geoserver_layer_exists:
                    command = self.get_worker().delete_datasource
            else:
                pass

        if command is not None:
            self.put_on_a_queue(context, 'resource', command, resource_dict, dataset_dict, None, None)

        pass

    # Hooks in use ****************************************************************************************
    def action_to_take_on_package_delete(self, context, package):
        """
        Checks if the cleanup of Geoserver for items related to this package is needed.
        Returns True when:
            "geoserver_link_enabled" == True AND Package has resources
        """
        if link_is_enabled(package, 'geoserver_link_enabled'):
            log.debug('delete_package triggered because geoserver_link_enabled is True')
            return self.get_worker().delete_package
        return None

    def action_to_take_on_package_purge(self, context, package):
        """
        Checks if the cleanup of Geoserver for items related to this package is needed.
        Returns True when:
            "geoserver_link_enabled" == True AND Package has resources
        """
        return self.action_to_take_on_package_delete(context, package)

    def action_to_take_on_resource_update(self, context, resource, resource_changes, package, package_changes):
        link_enabled = link_is_enabled(package, 'geoserver_link_enabled')
        if 'geoserver_link_enabled' in package_changes:
            layer_exists = resource.get('format', None) not in ['wms', 'wfs'] and \
                                     resource.get("wfs_url", None) and resource.get("wms_url", None)
            fields = ['name', 'description', 'layer_extent', 'layer_srid']
            valid_resource = all([resource.get(field, None) for field in fields])
            log.info("{} :: action_to_take_on_resource_update :: link_enabled = {}, layer_exists = {}, valid_resource = {}".format(
                self.name, link_enabled, layer_exists, valid_resource
            ))
            if link_enabled and valid_resource:
                log.info("")
                return self.get_worker().create_datasource
            if not link_enabled and layer_exists:
                return self.get_worker().delete_datasource
        elif link_enabled and resource_changes:
            return self.get_worker().create_datasource
        return None

    def action_to_take_on_resource_delete(self, context, resource, package):
        """
        Call geoserver.DELETE_Layer when:
            - Package."geoserver_link_enabled" == True AND
            - Necessary resource fields that matter to Geoserver available/valid
        """
        layer_exists = resource.get('format', None) not in ['wms', 'wfs'] and resource.get("wfs_url", None) and resource.get("wms_url", None)
        if layer_exists:
            return self.get_worker().delete_datasource

    def action_to_take_on_resource_purge(self, context, resource, package):
        return self.action_to_take_on_resource_delete(context, resource, package)

    # def does_resource_exist(self, res_dict, pkg_dict):
    #     correct_format = res_dict.get('format', None) not in ['wms', 'wfs']
    #     fields_filled = bool(res_dict.get("wfs_url", None)) and bool(res_dict.get("wms_url", None))
    #     return correct_format and fields_filled
    #
    # def should_resource_exist(self, res_dict, pkg_dict):
    #     active_resource = res_dict.get("state", None) == "active"
    #     active_package = pkg_dict.get("state", None) == "active"
    #     link_enabled = link_is_enabled(pkg_dict, 'geoserver_link_enabled')
    #     fields = ['name', 'description', 'layer_extent', 'layer_srid']
    #     valid_resource = all([res_dict.get(field, None) for field in fields])
    #     return active_resource and active_package and link_enabled and valid_resource
    #
    # def action_on_package_create(self):
    #     pass
    #
    # def action_on_package_update(self):
    #     pass
    #
    # def action_on_package_delete(self):
    #     pass
    #
    # def action_on_package_purge(self):
    #     pass
    #
    # def action_on_resource_create(self):
    #     pass
    #
    # def action_on_resource_update(self):
    #     pass
    #
    # def action_on_resource_delete(self):
    #     pass
    #
    # def action_on_resource_purge(self):
    #     pass
