import logging
import json

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
        self.put_on_a_queue(context, resource_dict, dataset_dict, self.get_worker().create_datasource)

    # Interface method not implemented
    # def can_upload(self, resource_id):
    #     return True

    def put_on_a_queue(self, context, resource_dict, dataset_dict, command):
        q = Queue(self.get_queue_name(), connection=self.redis_connection)
        configuration_data, package_data, resource_data, datadictionary_data = self.get_data(context, resource_dict)
        q.enqueue(command, configuration_data, package_data, resource_data, datadictionary_data)

    def get_data(self, context, resource):
        # Configuration data
        configuration_data = self.get_configuration_data(context)
        # Include package data (GeoNetwork worker needs package information at resource level)
        if resource.get('package_id'):
            package_data = self.get_package_data(context, resource['package_id'])
        else:
            package_data = None
        # Resource data
        resource_data = self.get_resource_data(context, resource['id'])
        # Data Dictionary data
        datadictionary_data = self.get_datadictionary_data(context, resource['id'])
        return configuration_data, package_data, resource_data, datadictionary_data