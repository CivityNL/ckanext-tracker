import logging

from ckanext.tracker_base.package_resource_tracker import PackageResourceTrackerPlugin
from worker.ckan_to_ckan import CkanToCkanWorkerWrapper

log = logging.getLogger(__name__)


class CkanToCkanTrackerPlugin(PackageResourceTrackerPlugin):
    """This is a base PackageTrackerPlugin which can be used for a CKAN to CKAN connection.
    As such it should NOT be used directly. The show_badge is by default True
   """

    worker = CkanToCkanWorkerWrapper()
    show_badge = True
