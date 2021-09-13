import logging

from ckanext.tracker.classes.datastore_tracker import DataStoreTrackerPlugin
from worker.geoserver import GeoServerWorkerWrapper

log = logging.getLogger(__name__)


# IS THIS TRACKER EVEN USED/ACTIVE? IT DOEST NOT SEEM TO DO ANYTHING
class Datastoretracker_GeoserverPlugin(DataStoreTrackerPlugin):
    """No idea what the use is of this Tracker. If you know please add it here"""

    queue_name = 'geoserver'
    worker = GeoServerWorkerWrapper()
    geoserver_link_field_name = 'geoserver_link_enabled'

    def after_upload(self, context, resource_dict, dataset_dict):
        pass
        # if self.geoserver_link_field_name in dataset_dict and dataset_dict[self.geoserver_link_field_name] == 'True':
        #     log.info('Linking to Geoserver')
        #     # TODO harmonize before sending to worker
        #     self.put_on_a_queue(context, resource_dict, dataset_dict, self.get_worker().create_datasource)
