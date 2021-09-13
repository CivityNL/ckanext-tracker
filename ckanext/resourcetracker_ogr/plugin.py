import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import logic.action.update as action_update
import logic.auth.update as auth_update
from ckan import model
# from ckanext.resourcetracker_ogr.interface import IOgr
from ckanext.tracker.classes.resource_tracker import ResourceTrackerPlugin
from worker.ogr import OgrWorkerWrapper

import logging
logging.basicConfig()
log = logging.getLogger(__name__)


# TODO move this away from trackers, and put it in the project 'ckanext-ogrloader'
class Resourcetracker_OgrPlugin(ResourceTrackerPlugin):
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
    # plugins.implements(IOgr)

    queue_name = 'ogr'
    worker = OgrWorkerWrapper()

    # IDomainObjectModification
    # IResourceUrlChange
    def notify(self, entity, operation=None):
        if isinstance(entity, model.Resource):
            log.debug('[notify] entity.url_type = {} '.format(entity.url_type))
            if entity.url_type in ('datapusher', 'xloader', 'datastore'):
                log.debug('Skipping putting the resource {r.id} through OGR because '
                          'url_type "{r.url_type}" means resource.url '
                          'points to the datastore already, so loading '
                          'would be circular.'.format(r=entity))
                return

            if operation == model.domain_object.DomainObjectOperation.new or not operation:
                context = {'model': model, 'ignore_auth': True, 'defer_commit': True, 'user': 'automation'}
                self.put_resource_on_a_queue(context, entity.as_dict(), self.get_worker().create_resource)

    # IActions

    def get_actions(self):
        return {
            'ogr_can_upload_hook': action_update.ogr_can_upload_hook,
            'ogr_after_upload_hook': action_update.ogr_after_upload_hook
        }

    # IAuthFunctions

    def get_auth_functions(self):
        return {
            'ogr_can_upload_hook': auth_update.ogr_can_upload_hook,
            'ogr_after_upload_hook': auth_update.ogr_after_upload_hook
        }

    # IResourceController
    def after_create(self, context, resource):
        pass

    def before_update(self, context, current, resource):
        pass

    def after_update(self, context, resource):
        pass

    # def after_upload(self, context, resource_dict, dataset_dict):
    #     log.info("after_upload(resource_dict = '{}', dataset_dict = '{}')".format(resource_dict, dataset_dict))
    #     log.info("resource_id = {}".format(resource_dict.get("id")))
    #     log.info("datastore_active = {}".format(resource_dict.get("datastore_active")))
    #     data_dict = {"id": resource_dict.get("id")}
    #     resource_view_list = toolkit.get_action('resource_view_list')(context, data_dict)
    #     log.info(resource_view_list)
    #     view_plugins = [plugin for plugin in plugins.PluginImplementations(plugins.IResourceView)]
    #     for current_view in resource_view_list:
    #         for view_plugin in view_plugins:
    #             if current_view.get("view_type") == view_plugin.name or current_view.get("view_type") == view_plugin.info().get("name"):
    #                 log.info(current_view)
    #                 log.info(view_plugin)
    #                 if not view_plugin.can_view({'resource': resource_dict, 'package': dataset_dict}):
    #                     r = toolkit.get_action('resource_view_delete')(context, {"id": current_view.get("id")})
    #                     log.info(r)
    #                 log.info(view_plugin.can_view({'resource': resource_dict, 'package': dataset_dict}))
    #                 break
    #     log.info(view_plugins)
    #     data_dict = {'resource': resource_dict, 'package': dataset_dict}
    #     toolkit.get_action('resource_create_default_resource_views')(context, data_dict)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')

    # IRoutes

    def before_map(self, m):
        m.connect(
            'resource_data_ogr', '/dataset/{id}/resource_data/{resource_id}',
            controller='ckanext.resourcetracker_ogr.controllers:ResourceDataController',
            action='resource_data', ckan_icon='cloud-upload')
        return m
