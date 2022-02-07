from ckanext.tracker.classes.package_tracker import PackageTrackerPlugin
from worker.geoserver import GeoServerWorkerWrapper
from ckan.plugins.toolkit import get_action
import ckanext.tracker.classes.helpers as tracker_helpers

import logging
log = logging.getLogger(__name__)


class Packagetracker_GeoserverPlugin(PackageTrackerPlugin):
    """
    Trigger package CRUD for geoserver Worker
    """
    queue_name = 'geoserver'
    worker = GeoServerWorkerWrapper()

    def after_create(self, context, pkg_dict):
        pass

    def after_update(self, context, pkg_dict):
        '''
        monitor only geoserver_link_enabled change
        '''
        # only if the package metadata are changed, we want the worker triggered.
        # if resource metadata change, this is part of the resourcetracker
        if not pkg_dict.get('resources', None):
            self.put_package_on_a_queue(context, pkg_dict, self.do_update())

    def after_delete(self, context, pkg_dict):
        deleted_pkg_dict = get_action('package_show')(
            context, {'id': pkg_dict.get('id')})
        if tracker_helpers.geoserver_link_is_enabled(deleted_pkg_dict):
            self.put_package_on_a_queue(context, pkg_dict, self.do_delete())
