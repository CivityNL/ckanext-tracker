import ckanext.datastoretracker.plugin as datastoretracker
from worker.geoserver import GeoServerWorkerWrapper
import logging

log = logging.getLogger(__name__)


class Datastoretracker_GeoserverPlugin(datastoretracker.DatastoretrackerPlugin):

    queue_name = 'geoserver'
    worker = GeoServerWorkerWrapper()
    geoserver_link_field_name = 'geoserver_link_enabled'

    def after_upload(self, context, resource_dict, dataset_dict):
        pass
        # if self.geoserver_link_field_name in dataset_dict and dataset_dict[self.geoserver_link_field_name] == 'True':
        #     log.info('Linking to Geoserver')
        #     # TODO harmonize before sending to worker
        #     self.put_on_a_queue(context, resource_dict, dataset_dict, self.get_worker().create_datasource)
