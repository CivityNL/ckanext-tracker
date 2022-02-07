import logging
import ckan.plugins as plugins
from ckanext.tracker.classes.package_tracker import PackageTrackerPlugin
from worker.geonetwork import GeoNetworkWorkerWrapper
from ckan.plugins.toolkit import get_action
from ckan import model
import ckanext.tracker.classes.helpers as tracker_helpers
log = logging.getLogger(__name__)


class Packagetracker_GeonetworkPlugin(PackageTrackerPlugin):
    """
    Trigger package CRUD for NGR Worker
    """
    # plugins.implements(plugins.IDomainObjectModification)
    queue_name = 'geonetwork'
    worker = GeoNetworkWorkerWrapper()

    def after_create(self, context, pkg_dict):
        pass

    def after_update(self, context, pkg_dict):
        # only if the package metadata are changed, we want the worker triggered.
        # if resource metadata change, this is part of the resourcetracker
        self.put_package_on_a_queue(context, pkg_dict, self.do_update())

    def after_delete(self, context, pkg_dict):
        deleted_pkg_dict = get_action('package_show')(
            context, {'id': pkg_dict.get('id')})
        if tracker_helpers.geonetwork_link_is_enabled(deleted_pkg_dict):
            self.put_package_on_a_queue(context, pkg_dict, self.do_delete())
