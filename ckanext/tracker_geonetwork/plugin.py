import ckan.plugins.toolkit as toolkit
from ckanext.tracker_base import PackageResourceTrackerPlugin
from ckanext.tracker_geonetwork.helpers import geonetwork_link_is_enabled
from worker.geonetwork import GeoNetworkWorkerWrapper
import ckan.plugins as plugins
import logic.action.update as action_update
import logic.auth.update as auth_update
from ckanext.tracker_geoserver.interface import ITrackerGeoserver
from ckanext.tracker_base.helpers import link_is_enabled
import logging

logging.basicConfig()
log = logging.getLogger(__name__)


class GeonetworkTrackerPlugin(PackageResourceTrackerPlugin):
    """
    This Tracker basically does nothing tracking wise except for UI changes and the after_show for a resource to return
    the geonetwork URL of this resource. To prevent accessing the geonetwork for every single after_show a cache can be
    activated by setting 'local_cache_active' to True (or by using 'ckanext.{}.geonetwork.local_cache_active' in the ini).
    This will then get all the identifiers from the source every 'local_cache_refresh_rate' seconds, except if the
    requested resource has been updated since the last refresh
    """
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(ITrackerGeoserver)

    queue_name = 'geonetwork'
    worker = GeoNetworkWorkerWrapper()

    local_cache_active = False
    local_cache_refresh_rate = 300
    local_cache = {}
    local_cache_last_updated = {}
    local_cache_thread_active = {}

    DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

    exclude_resource_fields = ["wfs_url", "wms_url"]

    # IConfigurable
    def configure(self, config):
        super(GeonetworkTrackerPlugin, self).configure(config)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')

    # IActions
    def get_actions(self):
        actions = super(GeonetworkTrackerPlugin, self).get_actions()
        actions.update({'geonetwork_callback_hook': action_update.geonetwork_callback_hook})
        return actions

    # IAuthFunctions
    def get_auth_functions(self):
        return {'geonetwork_callback_hook': auth_update.geonetwork_callback_hook}

    # Hooks in use ****************************************************************************************
    def action_to_take_on_package_delete(self, context, package):
        if geonetwork_link_is_enabled(package):
            log.debug('package_delete triggered because geonetwork_link_is_enabled is True')
            return self.get_worker().delete_package
        return None

    def action_to_take_on_package_purge(self, context, package):
        return self.action_to_take_on_package_delete(context, package)

    def action_to_take_on_resource_update(self, context, resource, resource_changes, package, package_changes):
        if 'geonetwork_link_enabled' in package_changes:
            link_enabled = link_is_enabled(package, 'geonetwork_link_enabled')
            layer_exists = resource.get("geonetwork_url", None)
            fields = ['wfs_url', 'wms_url']
            valid_resource = all([resource.get(field, None) for field in fields])
            if link_enabled and valid_resource:
                return self.get_worker().create_datasource
            if not link_enabled and layer_exists:
                return self.get_worker().delete_datasource
        return None

    def action_to_take_on_resource_delete(self, context, resource, package):
        layer_exists = resource.get("geonetwork_url", None)
        if layer_exists:
            return self.get_worker().delete_datasource

    def action_to_take_on_resource_purge(self, context, resource, package):
        return self.action_to_take_on_resource_delete(context, resource, package)

    # ITrackerGeoserver
    def callback(self, context, state, resource_dict, dataset_dict):
        """
        Does not represent the cases where the creation of a resource is preceded by an already existing datastore table
        and in those cases the link should be checked
        """
        # TODO Digest callback value and implement each alternative
        # TODO Call do_resource_update or do_resource_delete or do nothing
        command = None
        link_enabled = link_is_enabled(dataset_dict, 'geonetwork_link_enabled')
        layer_exists = resource_dict.get("geonetwork_url", None)
        fields = ['wfs_url', 'wms_url']
        valid_resource = all([resource_dict.get(field, None) for field in fields])
        log.debug("state = {} link_enabled = {} layer_exists = {} valid_resource = {}".format(
            state, link_enabled, layer_exists, valid_resource
        ))
        if link_enabled:
            if state == 'created':
                if valid_resource:
                    command = self.get_worker().create_datasource
            elif state == 'updated':
                if valid_resource:
                    command = self.get_worker().create_datasource
                elif layer_exists:
                    command = self.get_worker().delete_datasource
            elif state == 'deleted':
                if layer_exists:
                    command = self.get_worker().delete_datasource
            else:
                pass

        if command is not None:
            self.put_on_a_queue(context, 'resource', command, resource_dict, dataset_dict, None, None)

        pass
