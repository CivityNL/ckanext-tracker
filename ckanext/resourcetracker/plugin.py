import logging
import json

from rq import Queue
from redis import Redis

from ckan.common import config

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import ckanext.tracker.plugin as tracker

logging.basicConfig()
log = logging.getLogger(__name__)


class ResourcetrackerPlugin(tracker.TrackerPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IResourceController, inherit=True)

    queue_name = 'undefined'

    worker = None

    redis_connection = Redis('redis', 6379)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'resourcetracker')

    # IResourceController

    def after_create(self, context, resource):
        log.info('after_create from {}, action: {}'.format(__name__, 'none'))
        self.put_on_a_queue(context, resource, self.get_worker().create_resource)

    def after_update(self, context, resource):
        log.info('after_update from {}, action: {}'.format(__name__, 'none'))
        self.put_on_a_queue(context, resource, self.get_worker().update_resource)

    def before_delete(self, context, resource, resources):
        log.info('before_delete from {}, action: {}'.format(__name__, 'none'))
        self.put_on_a_queue(context, resource, self.get_worker().delete_resource)

    def put_on_a_queue(self, context, resource, command):
        q = Queue(self.get_queue_name(), connection=self.redis_connection)
        configuration_data, package_data, resource_data = self.get_data(context, resource)
        q.enqueue(command, configuration_data, package_data, resource_data)

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

        return configuration_data, package_data, resource_data
