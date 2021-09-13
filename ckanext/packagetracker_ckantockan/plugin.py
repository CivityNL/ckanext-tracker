import logging

from ckanext.tracker.classes.package_tracker import PackageTrackerPlugin
from worker.ckan_to_ckan import CkanToCkanWorkerWrapper

log = logging.getLogger(__name__)


class Packagetracker_CkantockanPlugin(PackageTrackerPlugin):
    """This is a base PackageTrackerPlugin which can be used for a CKAN to CKAN connection.
    As such it should NOT be used directly. The show_badge is by default True
   """

    worker = CkanToCkanWorkerWrapper()
    show_badge = True

    def do_delete(self):
        return self.do_purge()
