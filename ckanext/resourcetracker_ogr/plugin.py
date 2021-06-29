from ckan import model
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.resourcetracker.plugin as resourcetracker
import logic.auth.update as auth_update
import logic.action.update as action_update
from domain import Configuration
from worker.ogr import OgrWorkerWrapper
import logging

logging.basicConfig()
log = logging.getLogger(__name__)


# TODO move this away from trackers, and put it in the project 'ckanext-ogrloader'
class Resourcetracker_OgrPlugin(resourcetracker.ResourcetrackerPlugin):
    plugins.implements(plugins.IDomainObjectModification)
    plugins.implements(plugins.IResourceUrlChange)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)

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
                self.put_on_a_queue(context, entity.as_dict(), self.get_worker().create_resource)

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

    def after_upload(self, context, resource_dict, dataset_dict):
        pass
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