import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import logic.action.update as action_update
import logic.auth.update as auth_update
from ckan import model
from ckan.model import Resource, Package
from ckanext.tracker.classes import PackageResourceTrackerPlugin
from ckanext.tracker_ogr.interface import ITrackerOgr
from worker.ogr import OgrWorkerWrapper
import ckanext.tracker.classes.helpers as helpers
from ckan.common import c

import logging

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
    plugins.implements(plugins.IRoutes, inherit=True)

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

    # IRoutes
    def before_map(self, m):
        m.connect(
            'resource_data_ogr', '/dataset/{id}/resource_data/{resource_id}',
            controller='ckanext.tracker_ogr.controllers:ResourceDataController',
            action='resource_data', ckan_icon='cloud-upload')

        # generate new file from datastore using ogr2ogr capabilities
        m.connect(
            'ogr_dump', '/ogr/dump/{resource_id}',
            controller='ckanext.tracker_ogr.controllers:ResourceDataController',
            action='ogr_dump'
        )
        return m

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
