import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import helpers

log = logging.getLogger(__name__)


class TrackerPlugin(plugins.SingletonPlugin):
    """
    This plugin will add UI for all the trackers based on the backend and the specific configuration of the trackers
    """

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IRoutes, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'get_tracker_badges': helpers.get_tracker_badges,
            'get_tracker_statuses': helpers.get_tracker_statuses
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
        return m
