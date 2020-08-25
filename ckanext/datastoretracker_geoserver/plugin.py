import ckanext.datastoretracker.plugin as datastoretracker
from worker.geoserver import GeoServerWorkerWrapper

class Datastoretracker_GeoserverPlugin(datastoretracker.DatastoretrackerPlugin):

    queue_name = 'geoserver'
    worker = GeoServerWorkerWrapper()
    