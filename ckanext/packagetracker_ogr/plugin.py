from ckanext.tracker.classes.package_tracker import PackageTrackerPlugin
from worker.ogr import OgrWorkerWrapper


# IS THIS TRACKER EVEN USED/ACTIVE
# http://localhost:5000/api/action/package_show?id=one
class Packagetracker_OgrPlugin(PackageTrackerPlugin):
    """No idea what the use is of this Tracker. If you know please add it here"""

    queue_name = 'ogr'
    worker = OgrWorkerWrapper()
