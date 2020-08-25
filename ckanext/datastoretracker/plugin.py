import logging

from rq import Queue

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.xloader.interfaces as xloader_interfaces
import ckanext.datapusher.plugin as datapusher

import ckanext.tracker.plugin as tracker

from worker.geoserver import GeoServerWorkerWrapper

logging.basicConfig()
log = logging.getLogger(__name__)


class DatastoretrackerPlugin(tracker.TrackerPlugin):

    if plugins.plugin_loaded('datapusher'):
        plugins.implements(datapusher.IDataPusher, inherit=True)
    elif plugins.plugin_loaded('xloader'):
        plugins.implements(xloader_interfaces.IXloader, inherit=True)
    else:
        raise toolkit.ValidationError(
            {'Plugin': ['DataPusher or Xloader Extension must be enabled']})

    queue_name = 'undefined'
    
    worker = None

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'datastoretracker')

    # IXloader/IDataPusher
    # Both Extensions have the same Interface hook points, check docs:
    # https://github.com/ckan/ckan/blob/master/ckanext/datapusher/interfaces.py
    # https://github.com/ckan/ckanext-xloader/blob/master/ckanext/xloader/interfaces.py

    def after_upload(self, context, resource_dict, dataset_dict):
        log.info('after_upload from {}, action: {}'.format(__name__, 'none'))
        get_worker_create = self.get_worker().create_datasource
        if self.queue_name == 'geoserver':
            get_worker_create = self.get_worker().create_resource
        self.put_on_a_queue(context, resource_dict, dataset_dict,
                            get_worker_create)

    # Interface method not implemented
    # def can_upload(self, resource_id):
    #     return True

    def put_on_a_queue(self, context, resource_dict, dataset_dict, command):
        q = Queue(self.get_queue_name(), connection=self.redis_connection)
        conf_data = self.get_configuration_data(context)
        q.enqueue(command, conf_data, resource_dict, dataset_dict)
