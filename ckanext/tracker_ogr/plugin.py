import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import logic.action.update as action_update
import logic.auth.update as auth_update
from ckan import model
from ckan.model import Resource, Package
from ckanext.tracker.classes import BaseTrackerPlugin
from ckanext.tracker_ogr.interface import ITrackerOgr
from worker.ogr import OgrWorkerWrapper
import ckanext.tracker.classes.helpers as helpers
from ckan.common import c

import logging

logging.basicConfig()
log = logging.getLogger(__name__)


# TODO move this away from trackers, and put it in the project 'ckanext-ogrloader'
class OgrTrackerPlugin(BaseTrackerPlugin):
    """
    This beast of a Tracker is the replacement of the xloader/datapusher etc using the ogr2ogr command to push data to
    the datastore. It has its own Interface which can be triggerd by the extra hook actions which should also work with
    'old' setups
    """
    plugins.implements(plugins.IDomainObjectModification)
    plugins.implements(plugins.IResourceUrlChange)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IMapper, inherit=True)

    queue_name = 'ogr'
    worker = OgrWorkerWrapper()

    ignore_resources = True
    ignore_packages = True

    # IDomainObjectModification & IResourceUrlChange
    def notify(self, entity, operation=None):

        # TODO Checks to act on Notify:
        # is it supported by the OGR
        # Is it an Upload
        # Did the file changed (resource.hash and resource.size)
        # TODO later Is/was Datastore Active
        # Resource Changed Format

        format_to_extension_mapping = {
            "csv": "csv",
            "dgn": "dgn",
            "geojson": "json",
            "json": "json",
            "gpkg": "gpkg",
            "shape/zip": "zip",
            "shape-zip": "zip",
            "zip": "zip",
            "xls": "xls",
            "xlsx": "xlsx"
        }

        if isinstance(entity, model.Resource):
            if entity.url_type in ('datapusher', 'xloader', 'datastore'):
                log.debug('Skipping putting the resource {r.id} through OGR because '
                          'url_type "{r.url_type}" means resource.url '
                          'points to the datastore already, so loading '
                          'would be circular.'.format(r=entity))
                return

            # IDomainObjectModification == NEW and IResourceUrlChange Route
            # TODO adjust if statement to match this scenario bellow
            # if resource_create or (resource update with url in resource_changes):
            if operation == model.domain_object.DomainObjectOperation.new or not operation:
                revision_id = helpers.get_revision_id({'model': model, 'session': model.Session, 'user': c.user})
                resource_changes = helpers.get_resource_changes(revision_id, entity.id)
                if operation == model.domain_object.DomainObjectOperation.new or 'size' in resource_changes or 'hash' in resource_changes or 'format' in resource_changes:
                    log.debug('OGR create_resource put on queue :: changes = {}'.format(resource_changes))
                    context = {'model': model, 'ignore_auth': True, 'defer_commit': True, 'user': 'automation'}
                    pkg_dict = toolkit.get_action("package_show")(context, {"id": entity.package_id})
                    self.put_on_a_queue(context, 'resource', self.get_worker().create_resource, entity.as_dict(), pkg_dict, None, None)
                else:
                    log.debug('NO REASON FOR OGR create_resource put on queue :: changes = {}'.format(resource_changes))

    # IActions
    def get_actions(self):
        return {
            'ogr_callback_hook': action_update.ogr_callback_hook
        }

    # IAuthFunctions
    def get_auth_functions(self):
        return {
            'ogr_callback_hook': auth_update.ogr_callback_hook
        }

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')

    # IRoutes
    def before_map(self, m):
        m.connect(
            'resource_data_ogr', '/dataset/{id}/resource_data/{resource_id}',
            controller='ckanext.tracker_ogr.controllers:ResourceDataController',
            action='resource_data', ckan_icon='cloud-upload')
        return m

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

    # IMapper
    def after_delete(self, mapper, connection, instance):
        if mapper.entity == Resource:
            helpers.purge_task_statuses(connection, instance.id, 'resource', self.name)
        elif mapper.entity == Package:
            helpers.purge_task_statuses(connection, instance.id, 'package', self.name)
