import ckanext.resourcetracker.plugin as resourcetracker
from worker.ogr import OgrWorkerWrapper


class Resourcetracker_OgrPlugin(resourcetracker.ResourcetrackerPlugin):

    queue_name = 'ogr'
    worker = OgrWorkerWrapper()
