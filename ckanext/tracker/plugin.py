import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultTranslation
import helpers
from ckanext.tracker.backend import TrackerBackend

log = logging.getLogger(__name__)


class TrackerPlugin(plugins.SingletonPlugin, DefaultTranslation):
    """
    This plugin will add UI for all the trackers based on the backend and the specific configuration of the trackers
    """
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IRoutes, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_resource('fanstatic', 'tracker')

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'get_trackers': TrackerBackend.get_trackers,
            'get_tracker_badges': helpers.get_tracker_badges,
            'get_tracker_statuses': helpers.get_tracker_statuses,
            'get_tracker_activities': helpers.get_tracker_activities,
            'get_tracker_activities_stream': helpers.get_tracker_activities_stream,
            'get_tracker_queues': helpers.get_tracker_queues,
            'hash': helpers.hash
        }

    # IRoutes

    def before_map(self, m):
        m.connect(
            'resource_trackers', '/dataset/{id}/resource/{resource_id}/trackers',
            controller='ckanext.tracker.controllers:TrackerController',
            action='resource_data', ckan_icon='share')
        m.connect(
            'package_trackers', '/dataset/{id}/trackers',
            controller='ckanext.tracker.controllers:TrackerController',
            action='package_data', ckan_icon='share')
        m.connect(
            'admin.trackers', '/ckan-admin/trackers',
            controller='ckanext.tracker.controllers:TrackerController',
            action='queues')
        return m
