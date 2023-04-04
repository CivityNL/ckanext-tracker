import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultTranslation
import ckanext.tracker.helpers as helpers
from ckanext.tracker_base.backend import TrackerBackend
import ckanext.tracker.views as views

log = logging.getLogger(__name__)


class TrackerPlugin(plugins.SingletonPlugin, DefaultTranslation):
    """
    This plugin will add UI for all the trackers based on the backend and the specific configuration of the trackers
    """
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_resource('public', 'ckanext-tracker')

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

    # IBlueprint
    def get_blueprint(self):
        u'''Return a Flask Blueprint object to be registered by the app.'''
        return views.tracker
