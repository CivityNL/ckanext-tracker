import json
import logging
import re

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.tracker.backend import TrackerBackend
from domain import Configuration, Package, Resource
from helpers import get_configuration_dict, get_action_data, return_data, create_task, update_task, upsert_task
from mapper.mapper import Mapper
from redis import Redis
from rq import Queue
from rq.job import Job

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


class BaseTrackerPlugin(plugins.SingletonPlugin):
    """
    This Plugin contains all the logic necessary to have access to the queues/workers/mappers, feedback and
    UI capabilities
    """
    plugins.implements(plugins.IConfigurable)

    queue_name = None
    configuration = None
    worker = None
    redis_connection = None
    mapper = None  # type: Mapper

    badge_title = None
    show_ui = True
    show_badge = False

    # IConfigurable

    def configure(self, config):
        """
        Registering to the backend and setting values on load
        """
        self.register()
        if self.queue_name is None:
            self.queue_name = self.name
        self.redis_connection = set_connection()
        self.configuration = Configuration.from_dict(get_configuration_dict(self.name))

    def get_configuration_data(self, context):
        configuration_data = Configuration.to_dict(self.get_configuration())
        return return_data(configuration_data)

    def get_package_data(self, context, package_id):
        """
        Ugly method for getting the package data from a package_show and adding information from the organization. If a
        mapper is given will map to harmonized
        """
        # Get package data. Contains organization without GeoNetwork URL and credentials (since these are added using a custom schema)
        package_data = get_action_data('package_show', context, {'id': package_id})
        # TODO get harmonized_package_show
        # package_data = self.get_action_data('harmonized_package_show', context, {'id': package_id})
        license_list = get_action_data('license_list', context, {})
        # Get the first element from the licence list, that matches the license ID and return it's URL
        package_data['license_url'] = next((license.get('url', None) for license in license_list if
                                            license["id"] == package_data.get('license_id', None)), None)
        # Get the organization with GeoNetwork URL and credentials
        if package_data is not None:
            organization_data = get_action_data('organization_show',
                                                context,
                                                {'id': package_data.get('organization', {}).get('id', None)}
                                                )
            if organization_data is not None:
                # Include the GeoNetwork URL and credentials in the organization in the package
                package_data['organization']['geonetwork_url'] = organization_data.get('geonetwork_url', None)
                package_data['organization']['geonetwork_password'] = organization_data.get('geonetwork_password', None)
                package_data['organization']['geonetwork_username'] = organization_data.get('geonetwork_username', None)
            else:
                if not package_data.get('organization', None):
                    package_data['organization'] = dict()
                package_data['organization']['geonetwork_url'] = None
                package_data['organization']['geonetwork_password'] = None
                package_data['organization']['geonetwork_username'] = None
        if self.mapper is not None:
            package = Package.from_dict(package_data)
            result = self.mapper.map_package_to_harmonized(self.get_configuration(), Package.to_dict(package))
        else:
            result = return_data(package_data)
        return result

    def get_resource_data(self, context, resource_id):
        """
        Method for getting the resource data. If a mapper is given will map to harmonized
        """
        resource_data = get_action_data('resource_show', context, {'id': resource_id})
        if self.mapper is not None:
            resource = Resource.from_dict(resource_data)
            result = self.mapper.map_resource_to_harmonized(self.get_configuration(), Resource.to_dict(resource))
        else:
            result = return_data(resource_data)
        return result

    def get_datadictionary_data(self, context, resource_id):
        # use the datastore_search api without records (limit 0) to get the dictionary settings
        datadictionary_data = get_action_data('datastore_search', context, {'id': resource_id, 'limit': 0})
        return return_data(datadictionary_data)

    def put_on_a_queue(self, context, entity_type, data, command):
        """
        This method will make sure a job is created and put on the queue and giving the correct feedback
        """
        task = None
        try:
            job = self.create_job(context, entity_type, data, command)
            self.before_enqueue(context, data, job)
            task = upsert_task(context, self.name, entity_type, data, job)
            q = Queue(self.get_queue_name(), connection=self.get_connection())
            q.enqueue_job(job)
            if task is not None:
                update_task(context, task.get("id"), state="pending")
            self.after_enqueue(context, data, job)
        except TrackerPluginException as error:
            log.warning("An expected error occured: {}".format(error.message))
            self.handle_error(context, data, command, error)
        except Exception as unexpected_error:
            log.error("An unexpected error occured: {}".format(unexpected_error.message))
            if task is not None:
                update_task(context, task.get("id"), state="error", error=unexpected_error.message)

    def create_job(self, context, entity_type, data, command):
        """
        This method will create the Job to be put on the queue based on all the information
        """
        cfg = self.get_configuration()
        return Job.create(
            command,
            args=self.get_data(context, entity_type, data),
            connection=self.get_connection(),
            timeout=cfg.redis_job_timeout,
            result_ttl=cfg.redis_job_result_ttl,
            ttl=cfg.redis_job_ttl,
            description='Job created by {}'.format(self.name)
        )

    def get_data(self, context, entity_type, data):
        """
        This method will create all the data necessary for the Job and worker commands
        """
        is_data_dict = isinstance(data, dict)
        resource_id = None
        package_id = None
        if entity_type == 'package':
            if is_data_dict:
                package_id = data.get('id', None)
            else:
                package_id = data
        if entity_type == 'resource' or entity_type == 'datastore':
            if is_data_dict:
                resource_id = data.get('id', None)
                package_id = data.get('package_id', None)
            else:
                resource_id = data

        configuration_data = None
        resource_data = None
        data_dictionary_data = None
        package_data = None

        # Configuration data
        configuration_data = self.get_configuration_data(context)
        if resource_id is not None:
            resource_data = self.get_resource_data(context, resource_id)
            data_dictionary_data = self.get_datadictionary_data(context, resource_id)
        if package_id is not None:
            package_data = self.get_package_data(context, package_id)

        # the package commands of the worker require a different set of data then the resource/datastore commands
        if entity_type == 'package':
            return configuration_data, package_data
        if entity_type == 'resource' or entity_type == 'datastore':
            return configuration_data, package_data, resource_data, data_dictionary_data

    def before_enqueue(self, context, data, job):
        """
        This method will be executed just before the actual enqueueing is done. By throwing TrackerPluginExceptions the
        normal flow can be broken in case if the data does not confirm to certain checks etc
        """
        pass

    def after_enqueue(self, context, data, job):
        """
        This method will be executed after the job is enqueued.
        """
        pass

    def handle_error(self, context, data, command, error):
        """
        All TrackerPluginExceptions thrown before or during the enqueueing could be handled here
        """
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

    def get_types(self):
        return []

    def get_badge_title(self):
        """
        Ths method will return the badge title, first from the ini file with the class property as default
        """
        return toolkit.config.get(
            'ckanext.{}.badge_title'.format(self.name), self.badge_title
        )

    def register(self):
        """
        Say hello to the backend!
        """
        TrackerBackend.register(self)

    def get_show_ui(self, context, entity_type, entity_id_or_dict):
        """
        This method checks if the UI should be shown for this tracker
        """
        show_ui = toolkit.config.get(
            'ckanext.{}.show_ui'.format(self.name), self.show_ui
        )
        if not show_ui:
            return False

    def add_get_show(self, context, entity_type, entity_id_or_dict, _type, _action, _method):
        """
        This method is a wrapper to 'simple' add new *_get_show 'switches'. E.g. if a entity_type of 'X' based on the
        dictionary information from the CKAN action 'X_show' should be checked by the method 'show_*_for_type_X' this
        can be used a "self.add_get_show(context, entity_type, entity_id_or_dict, 'X', 'X_show', self.show_*_for_type_X)
        See also the PackageTrackerPlugin and ResourceTrackerPlugin as examples
        """
        is_entity_dict = isinstance(entity_id_or_dict, dict)
        entity = entity_id_or_dict
        if entity_type == _type:
            if not is_entity_dict:
                entity = toolkit.get_action(_action)(context, {'id': entity})
            return _method(context, entity)

    def get_show_badge(self, context, entity_type, entity_id_or_dict):
        """
        This method checks if the badge should be shown for this tracker
        """
        show_badge = toolkit.config.get(
            'ckanext.{}.show_badge'.format(self.name), self.show_badge
        )
        if not show_badge or self.get_badge_title() is None:
            return False
