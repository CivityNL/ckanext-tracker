import json

from redis import Redis
from domain import Configuration
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from rq import Queue
from rq.job import Job
import re

import logging
log = logging.getLogger(__name__)


def set_connection():
    """
    This function will get the Redis connection information from the configuration and initialize a
    Redis connection based on the host and port
    :return: Redis connection
    """
    redis_url = toolkit.config.get('ckan.redis.url', 'redis://localhost:6379/0')
    m = re.match(r'.+(?<=:\/\/)(.+)(?=:):(.+)(?=\/)', redis_url)
    redis_host = m.group(1)
    redis_port = int(m.group(2))
    return Redis(redis_host, redis_port)


class TrackerPluginException(Exception):
    pass


class TrackerPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigurable)

    queue_name = None
    configuration = None
    worker = None
    redis_connection = None

    # IConfigurable

    def configure(self, config):
        if self.queue_name is None:
            self.queue_name = self.name
        self.redis_connection = set_connection()
        self.configuration = Configuration.from_dict(self.get_configuration_dict())

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'tracker')

    def get_package_data(self, context, package_id):
        # Get package data. Contains organization without GeoNetwork URL and credentials (since these are added using a custom schema)
        package_data = toolkit.get_action('package_show')(context, {'id': package_id})

        # Get the organization with GeoNetwork URL and credentials
        organization_data = toolkit.get_action('organization_show')(context, {'id': package_data['organization']['id']})

        # Include the GeoNetwork URL and credentials in the organization in the package
        package_data['organization']['geonetwork_url'] = organization_data['geonetwork_url']
        package_data['organization']['geonetwork_password'] = organization_data['geonetwork_password']
        package_data['organization']['geonetwork_username'] = organization_data['geonetwork_username']

        return json.dumps(package_data)

    def get_configuration_data(self, context):
        configuration_data = json.dumps(self.get_configuration_dict())
        return configuration_data

    def get_configuration_dict(self):
        conf_dict = {
            "database_url": toolkit.config.get(
                'ckan.datastore.write_url'
            ),
            "geoserver_url": toolkit.config.get(
                'ckanext.{}.geoserver.url'.format(self.name),
                None
            ), 
			"address": toolkit.config.get(
                'ckanext.{}.address'.format(self.name),
                "Handelsweg 6"
            ),
			"address_city": toolkit.config.get(
                'ckanext.{}.address.city'.format(self.name),
                "Zeist"
            ),
            "address_country": toolkit.config.get(
                'ckanext.{}.address.country'.format(self.name),
                "the Netherlands"
            ),
			"address_phone": toolkit.config.get(
                'ckanext.{}.address.phone'.format(self.name),
                "+31 30 697 32 86"
            ),
			"address_state": toolkit.config.get(
                'ckanext.{}.address.state'.format(self.name),
                "Utrecht"
            ),
            "address_type": toolkit.config.get(
                'ckanext.{}.address.type'.format(self.name),
                "electronic"
            ),
			"address_zip_code": toolkit.config.get(
                'ckanext.{}.address.zip_code'.format(self.name),
                "3707 NH"
            ),
            "contact_email": toolkit.config.get(
                'ckanext.{}.contact.email'.format(self.name),
                "support@civity.nl"
            ),
            "contact_organization": toolkit.config.get(
                'ckanext.{}.contact.organization'.format(self.name),
                "Civity"
            ),
            "contact_person": toolkit.config.get(
                'ckanext.{}.contact.person'.format(self.name),
                "Mathieu Ronkes Agerbeek"
            ),
            "contact_position": toolkit.config.get(
                'ckanext.{}.contact.position'.format(self.name),
                "Support engineer"
            ),
            "contact_url": toolkit.config.get(
                'ckanext.{}.contact.url'.format(self.name),
                "https://civity.nl"
            ),
            "ogr2ogr_command": toolkit.config.get(
                'ckanext.{}.command.ogr2ogr'.format(self.name),
                "ogr2ogr"
            ),
            "remote_ckan_host": toolkit.config.get(
                'ckanext.{}.remote_ckan_host'.format(self.name)
            ),
            "remote_ckan_org": toolkit.config.get(
                'ckanext.{}.remote_ckan_org'.format(self.name)
            ),
            "remote_user_api_key": toolkit.config.get(
                'ckanext.{}.remote_user_api_key'.format(self.name)
            ),
            "source_ckan_host": toolkit.config.get(
                'ckanext.{}.source_ckan_host'.format(self.name)
            ),
            "source_ckan_org": toolkit.config.get(
                'ckanext.{}.source_ckan_org'.format(self.name)
            ),
            "source_ckan_user": toolkit.config.get(
                'ckanext.{}.source_ckan_user'.format(self.name)
            ),
            "source_user_api_key": toolkit.config.get(
                'ckanext.{}.source_user_api_key'.format(self.name)
            ),
            "storage_path": toolkit.config.get(
                'ckan.storage_path'
            ),
            "source_job_status_field": '{}_status'.format(self.name),
            "source_job_id_field": '{}_job_id'.format(self.name),
            "redis_job_timeout": toolkit.config.get(
                'ckanext.{}.redis_job_timeout'.format(self.name), 180),
            "redis_job_result_ttl": toolkit.config.get(
                'ckanext.{}.redis_job_result_ttl'.format(self.name), 500),
            "redis_job_ttl": toolkit.config.get(
                'ckanext.{}.redis_job_ttl'.format(self.name), None),
            "redis_url": toolkit.config.get(
                'ckan.redis.url', "redis://localhost:6379/")
        }
        return conf_dict

    def put_on_a_queue(self, context, data, command):
        try:
            job_data = self.get_data(context, data)
            job = self.create_job(context, job_data, command)
            self.before_enqueue(context, data, job)
            q = Queue(self.get_queue_name(), connection=self.get_connection())
            q.enqueue_job(job)
            self.after_enqueue(context, data, job)
        except TrackerPluginException as error:
            self.handle_error(context, data, command, error)

    def create_job(self, context, data, command):
        cfg = self.get_configuration()
        return Job.create(
            command,
            args=(cfg, data),
            connection=self.get_connection(),
            timeout=cfg.redis_job_timeout,
            result_ttl=cfg.redis_job_result_ttl,
            ttl=cfg.redis_job_ttl,
            description='Job created by {}'.format(self.name)
        )

    def get_data(self, context, data):
        return data

    def before_enqueue(self, context, data, job):
        pass

    def after_enqueue(self, context, data, job):
        pass

    def handle_error(self, context, data, command, error):
        pass

    # getters

    def get_queue_name(self):
        return self.queue_name

    def get_worker(self):
        return self.worker

    def get_connection(self):
        return self.redis_connection

    def get_configuration(self):
        return self.configuration
