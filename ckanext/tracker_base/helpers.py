import re
from redis import Redis
import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as toolkit
from domain import Package, Resource, DataDictionary
from sqlalchemy import and_
from ckan.model import task_status_table
from domain.task_status import DomainTaskStatus
from typing import Dict, Optional, List
from ckan.model import State

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


def get_user_apikey(user_id, target='source'):
    """
    This function will get the apikey for a specific user
    :return: apikey
    """
    try:
        if not user_id:
            return None
        user = model.User.get(user_id)
        if user:
            return user.apikey
    except:
        return None
    return None


def get_action_data(action, context, parameters):
    """
    This method is a wrapper around the toolkit.get_action which will check for any ActionErrors
    and if so will return a None object instead
    @param action:      action to perform
    @param context:     context for the action
    @param parameters:  specific parameters for the action
    @return:            either the result of the toolkit.get_action or None in case of an ActionError
    """
    action_data = None
    try:
        action_data = toolkit.get_action(action)(context, parameters)
    except logic.ActionError as actionError:
        pass
    return action_data


def link_is_enabled(data_dict, link_field_name):
    return link_field_name in data_dict and data_dict.get(link_field_name, None) == "True"


def raise_not_implemented_error(name):
    raise NotImplementedError(
        "{} :: This method needs to be implemented to specify what should happen when and how.".format(
            name
        ))


def has_been_deleted(object_dict, changes_dict):
    return object_dict.get("state", None) == State.DELETED and "state" in changes_dict


def is_active(object_dict):
    return object_dict.get("state", None) == State.ACTIVE


def _set_filtered_by_state(resources, state):
    return set([res_id for res_id in resources if resources[res_id].get("state", None) == state])


def get_ids_inserted_resources(before_resources, after_resources):
    before_ids = _set_filtered_by_state(before_resources, State.ACTIVE)
    after_ids = _set_filtered_by_state(after_resources, State.ACTIVE)
    return after_ids - before_ids


def get_ids_deleted_resources(before_resources, after_resources):
    before_ids = _set_filtered_by_state(before_resources, State.ACTIVE)
    after_ids = _set_filtered_by_state(after_resources, State.DELETED)
    return after_ids & before_ids


def get_ids_same_resources(before_resources, after_resources):
    before_ids = _set_filtered_by_state(before_resources, State.ACTIVE)
    after_ids = _set_filtered_by_state(after_resources, State.ACTIVE)
    return after_ids & before_ids


def compare_dicts(old_dict, new_dict, include_fields=None, exclude_fields=None):
    # type: (Dict[str, object], Dict[str, object], Optional[List[str]], Optional[List[str]]) -> Dict[str, Dict]

    result = {}
    if old_dict is not None and new_dict is not None:
        set_keys = set(old_dict.keys() + new_dict.keys())
        if include_fields is not None:
            set_keys = set_keys & set(include_fields)
        if exclude_fields is not None:
            set_keys = set_keys - set(exclude_fields)
        for key in set_keys:
            key_result = {}
            if key in old_dict and key not in new_dict:
                key_result['old'] = old_dict.get(key)
            elif key not in old_dict and key in new_dict:
                key_result['new'] = new_dict.get(key)
            else:
                old_value = old_dict.get(key)
                new_value = new_dict.get(key)
                if not old_value == new_value:
                    key_result['old'] = old_value
                    key_result['new'] = new_value
            if key_result:
                result[key] = key_result
    return result


def get_configuration_dict(name):
    DEFAULT_USERNAME = 'automation'
    DEFAULT_SOURCE_URL = toolkit.config.get('ckan.site_url')
    conf_dict = {
        "database_url": toolkit.config.get(
            'ckan.datastore.write_url'
        ),
        "geoserver_url": toolkit.config.get(
            'ckanext.{}.geoserver.url'.format(name),
            None
        ),
        "geonetwork_url": toolkit.config.get(
            'ckanext.{}.geonetwork.url'.format(name),
            None
        ),
        "address": toolkit.config.get(
            'ckanext.{}.address'.format(name),
            "Handelsweg 6"
        ),
        "address_city": toolkit.config.get(
            'ckanext.{}.address.city'.format(name),
            "Zeist"
        ),
        "address_country": toolkit.config.get(
            'ckanext.{}.address.country'.format(name),
            "the Netherlands"
        ),
        "address_phone": toolkit.config.get(
            'ckanext.{}.address.phone'.format(name),
            "+31 30 697 32 86"
        ),
        "address_state": toolkit.config.get(
            'ckanext.{}.address.state'.format(name),
            "Utrecht"
        ),
        "address_type": toolkit.config.get(
            'ckanext.{}.address.type'.format(name),
            "electronic"
        ),
        "address_zip_code": toolkit.config.get(
            'ckanext.{}.address.zip_code'.format(name),
            "3707 NH"
        ),
        "contact_email": toolkit.config.get(
            'ckanext.{}.contact.email'.format(name),
            "support@civity.nl"
        ),
        "contact_organization": toolkit.config.get(
            'ckanext.{}.contact.organization'.format(name),
            "Civity"
        ),
        "contact_person": toolkit.config.get(
            'ckanext.{}.contact.person'.format(name),
            "Mathieu Ronkes Agerbeek"
        ),
        "contact_position": toolkit.config.get(
            'ckanext.{}.contact.position'.format(name),
            "Support engineer"
        ),
        "contact_url": toolkit.config.get(
            'ckanext.{}.contact.url'.format(name),
            "https://civity.nl"
        ),
        "geonetwork_default_license_url": toolkit.config.get(
            'ckanext.{}.geonetwork.default_license_url'.format(name),
            None
        ),
        "geoserver_layer_prefix": toolkit.config.get(
            'ckanext.{}.geoserver.layer_prefix'.format(name),
            None
        ),
        "geoserver_resource_metadata": toolkit.config.get(
            'ckanext.{}.geoserver.resource_metadata'.format(name),
            None
        ),
        "ogr2ogr_command": toolkit.config.get(
            'ckanext.{}.command.ogr2ogr'.format(name),
            "ogr2ogr"
        ),
        "plugin_name": name,
        "remote_ckan_host": toolkit.config.get(
            'ckanext.{}.remote_ckan_host'.format(name)
        ),
        "remote_ckan_org": toolkit.config.get(
            'ckanext.{}.remote_ckan_org'.format(name)
        ),
        "remote_user_api_key": toolkit.config.get(
            'ckanext.{}.remote_user_api_key'.format(name)
        ),
        "remote_ckan_user": toolkit.config.get(
            'ckanext.{}.remote_ckan_user'.format(name)
        ),
        "source_ckan_host": toolkit.config.get(
            'ckanext.{}.source_ckan_host'.format(name), DEFAULT_SOURCE_URL
        ),
        "source_ckan_org": toolkit.config.get(
            'ckanext.{}.source_ckan_org'.format(name)
        ),
        "source_ckan_user": toolkit.config.get(
            'ckanext.{}.source_ckan_user'.format(name), DEFAULT_USERNAME
        ),
        "source_user_api_key": get_user_apikey(toolkit.config.get(
            'ckanext.{}.source_ckan_user'.format(name), DEFAULT_USERNAME)
        ),
        "storage_path": toolkit.config.get(
            'ckan.storage_path'
        ),
        "source_job_status_field": '{}_status'.format(name),
        "source_job_id_field": '{}_job_id'.format(name),
        "redis_job_timeout": toolkit.config.get(
            'ckanext.{}.redis_job_timeout'.format(name), 180),
        "redis_job_result_ttl": toolkit.config.get(
            'ckanext.{}.redis_job_result_ttl'.format(name), 500),
        "redis_job_ttl": toolkit.config.get(
            'ckanext.{}.redis_job_ttl'.format(name), None),
        "redis_url": toolkit.config.get(
            'ckan.redis.url', "redis://localhost:6379/")
    }
    return conf_dict


def get_package_data(context, configuration, mapper, pkg_dict):
    """
    Ugly method for getting the package data from a package_show and adding information from the organization. If a
    mapper is given will map to harmonized
    """
    license_list = get_action_data('license_list', context, {})
    # Get the first element from the licence list, that matches the license ID and return it's URL
    pkg_dict['license_url'] = next((license.get('url', None) for license in license_list if
                                    license["id"] == pkg_dict.get('license_id', None)), None)
    # Get the organization with GeoNetwork URL and credentials
    if pkg_dict is not None:
        organization_data = get_action_data('organization_show',
                                            context,
                                            {'id': pkg_dict.get('organization', {}).get('id', None)}
                                            )
        if organization_data is not None:
            # Include the GeoNetwork URL and credentials in the organization in the package
            pkg_dict['organization']['geonetwork_url'] = organization_data.get('geonetwork_url', None)
            pkg_dict['organization']['geonetwork_password'] = organization_data.get('geonetwork_password', None)
            pkg_dict['organization']['geonetwork_username'] = organization_data.get('geonetwork_username', None)
        else:
            if not pkg_dict.get('organization', None):
                pkg_dict['organization'] = dict()
            pkg_dict['organization']['geonetwork_url'] = None
            pkg_dict['organization']['geonetwork_password'] = None
            pkg_dict['organization']['geonetwork_username'] = None
    if mapper is not None:
        result = mapper.map_package_to_harmonized(configuration, pkg_dict)
    else:
        result = Package.from_dict(pkg_dict)
    return result


def get_resource_data(context, configuration, mapper, res_dict):
    """
    Method for getting the resource data. If a mapper is given will map to harmonized
    """
    if mapper is not None:
        result = mapper.map_resource_to_harmonized(configuration, res_dict)
    else:
        result = Resource.from_dict(res_dict)
    return result


def get_datadictionary_data(context, resource_id):
    # use the datastore_search api without records (limit 0) to get the dictionary settings
    data_dict = get_action_data('datastore_search', context, {'id': resource_id, 'limit': 0})
    return DataDictionary.from_dict(data_dict)


def get_data(context, configuration, entity_type, task_id, mapper, res_dict, pkg_dict):
    """
    This method will create all the data necessary for the Job and worker commands
    TODO document better params and return options
    """
    package = None
    resource = None
    data_dictionary = None
    configuration.task_status_id = task_id

    # Configuration data
    if res_dict is not None and entity_type == 'resource':
        resource = get_resource_data(context, configuration, mapper, res_dict)
        data_dictionary = get_datadictionary_data(context, resource.resource_id)
    if pkg_dict is not None:
        package = get_package_data(context, configuration, mapper, pkg_dict)

    # the package commands of the worker require a different set of data then the resource/datastore commands
    if entity_type == 'package':
        return configuration, package
    if entity_type == 'resource':
        return configuration, package, resource, data_dictionary


# Task Handling (see also `put_on_a_queue` method):
# DEV-3293 required feedback from the workers for which the TaskStatus model is being used and the corresponding
# `task_status_show` and `task_status_update` API actions. General idea is to have for each package/plugin and
# resource/plugin combination a TaskStatus which contains information about the current task being pending or
# executed (so no trail).

# Create a TaskStatus when none exist yet with the default value properties `job_id` and `job_command`
def create_task(context, job, task_type, entity_type, res_dict, pkg_dict):
    task = DomainTaskStatus(
        entity_id=res_dict.get("id") if entity_type == 'resource' else pkg_dict.get("id"),
        entity_type=entity_type,
        task_type=task_type,
        key=job.id, action=job.func_name
    )
    created_task_dict = get_action_data("task_status_update", context, task.to_dict())
    return DomainTaskStatus.from_dict(created_task_dict)


# Update a TaskStatus identified by task_id with a state (required), value properties and error message (optional).
# The value is a JSON stored as a string, which why the json module is involved in updating that field
def update_task(context, task, state, remote_id=None, error=None):
    result = None
    if task is not None:
        task.set_state(state, remote_id, error)
        task_dict = get_action_data("task_status_update", context, task.to_dict())
        result = DomainTaskStatus.from_dict(task_dict)
    return result


def show_task(context, task_id):
    task_dict = get_action_data("task_status_show", context, {"id": task_id})
    return DomainTaskStatus.from_dict(task_dict)


def purge_task_statuses(connection, entity_id, entity_type, task_type):
    connection.execute(
        task_status_table.delete().where(
            and_(
                task_status_table.c.entity_id == entity_id,
                task_status_table.c.entity_type == entity_type,
                task_status_table.c.task_type == task_type
            )
        )
    )
