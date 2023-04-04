import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.tracker_ogr.logic.action.update as action_update
import ckanext.tracker_ogr.logic.auth.update as auth_update
from ckan import model
from ckanext.tracker_base.package_resource_tracker import PackageResourceTrackerPlugin
from worker.ogr import OgrWorkerWrapper
import logging
import ckanext.tracker_ogr.views as views

logging.basicConfig()
log = logging.getLogger(__name__)


# TODO move this away from trackers, and put it in the project 'ckanext-ogrloader'
class OgrTrackerPlugin(PackageResourceTrackerPlugin):
    """
    This beast of a Tracker is the replacement of the xloader/datapusher etc using the ogr2ogr command to push data to
    the datastore. It has its own Interface which can be triggerd by the extra hook actions which should also work with
    'old' setups
    """

    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)

    queue_name = 'ogr'
    worker = OgrWorkerWrapper()

    ignore_resources = False
    ignore_packages = True
    separate_tracking = True

    include_resource_fields = ['url', 'size', 'hash', 'format']

    # IActions
    def get_actions(self):
        actions = super(OgrTrackerPlugin, self).get_actions()
        actions.update({'ogr_callback_hook': action_update.ogr_callback_hook})
        return actions

    # IAuthFunctions
    def get_auth_functions(self):
        return {
            'ogr_callback_hook': auth_update.ogr_callback_hook
        }

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')

    # IBlueprint
    def get_blueprint(self):
        u'''Return a Flask Blueprint object to be registered by the app.'''
        return views.create_blueprint(self)

    #  Return the action for each Hook - Default to None ***********************************
    def action_to_take_on_resource_create(self, context, res_dict, pkg_dict):
        context = {'model': model, 'ignore_auth': True, 'defer_commit': True, 'user': 'automation'}
        return self.put_on_a_queue(context, 'resource',
                                   self.get_worker().create_resource, res_dict, pkg_dict, None, None)

    def action_to_take_on_resource_update(self, context, res_dict, resource_changes, pkg_dict, package_changes):
        return self.action_to_take_on_resource_create(context, res_dict, pkg_dict)

    def action_to_take_on_resource_delete(self, context, res_dict, pkg_dict):
        if res_dict.get("datastore_active", False):
            context = {'model': model, 'ignore_auth': True, 'defer_commit': True, 'user': 'automation'}
            return self.put_on_a_queue(context, 'resource',
                                       self.get_worker().delete_resource, res_dict, pkg_dict, None, None)

    def action_to_take_on_resource_purge(self, context, res_dict, pkg_dict):
        return self.action_to_take_on_resource_delete(context, res_dict, pkg_dict)
