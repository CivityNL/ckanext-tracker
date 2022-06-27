from ..helpers import get_action_data, get_user_apikey
import logging
import ckan.plugins.toolkit as toolkit
from domain import Package, Resource, DataDictionary

log = logging.getLogger(__name__)


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
