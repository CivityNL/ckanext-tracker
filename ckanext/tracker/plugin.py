import json

from redis import Redis
from distutils.command.config import config

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


class TrackerPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)

    queue_name = 'undefined'

    worker = None

    redis_connection = Redis('redis', 6379)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'tracker')

    def get_configuration_data(self, context):
        cfg = {
            "database_url": toolkit.config.get(
                'ckan.datastore.write_url'
            ),
            "geoserver_url": toolkit.config.get(
                'ckanext.packagetracker_ogr.geoserver.url',
                "http://admin:geoserver@geoserver:8080/geoserver"
            ),
            "ogr2ogr_command": toolkit.config.get(
                'ckanext.packagetracker_ogr.command.ogr2ogr', "ogr2ogr"
            ),
            "remote_ckan_host": toolkit.config.get(
                'ckanext.packagetracker_ckantockan.remote_ckan_host',
                'http://192.168.99.100:5001'
            ),
            "remote_ckan_org": toolkit.config.get(
                'ckanext.packagetracker_ckantockan.remote_ckan_org',
                '6679c632-1b6d-47da-ae84-5c8a4d0ef806'
            ),
            "remote_user_api_key": toolkit.config.get(
                'ckanext.packagetracker_ckantockan.remote_user_api_key',
                '05a75583-1ed5-41ca-b630-6ff60922eb37'
            ),
            "source_ckan_host": toolkit.config.get(
                'ckanext.packagetracker_ckantockan.source_ckan_host',
                'http://192.168.99.100:5001'
            ),
            "source_ckan_org": toolkit.config.get(
                'ckanext.packagetracker_ckantockan.source_ckan_org',
                '6679c632-1b6d-47da-ae84-5c8a4d0ef806'
            ),
            "source_user_api_key": toolkit.config.get(
                'ckanext.packagetracker_ckantockan.source_user_api_key',
                '05a75583-1ed5-41ca-b630-6ff60922eb37'
            ),
            "storage_path": toolkit.config.get(
                'ckan.storage_path'
            )
        }
        configuration_data = json.dumps(cfg)
        return configuration_data

    def get_queue_name(self):
        return self.queue_name

    def get_worker(self):
        return self.worker
