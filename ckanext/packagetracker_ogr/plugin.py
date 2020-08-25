import ckanext.packagetracker.plugin as packagetracker
from worker.ogr import OgrWorkerWrapper


# http://localhost:5000/api/action/package_show?id=one
class Packagetracker_OgrPlugin(packagetracker.PackagetrackerPlugin):

    queue_name = 'ogr'
    worker = OgrWorkerWrapper()
