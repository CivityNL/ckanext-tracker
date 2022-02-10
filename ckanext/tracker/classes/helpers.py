import json
import logging
from datetime import date, datetime

import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as toolkit
from sqlalchemy.orm import aliased
from sqlalchemy.sql.functions import now

log = logging.getLogger(__name__)


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
        log.debug('get_action_data from {} returned {} for action: {}, context: {}, and parameters: {}'
                  .format(__name__, type(actionError).__name__, action, context, parameters))
    return action_data


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


def return_data(data):
    result = None
    if data is not None:
        # result = json.dumps(data)
        result = json.dumps(data, default=json_serial) # Fix TypeError: datetime.datetime(...) is not JSON serializable
    return result


def resource_get_changed_fields_after_update(res_dict):
    res_changes_dict = {}
    resource_id = res_dict.get("id", None)

    new_resource = model.Session.query(model.ResourceRevision). \
        filter(model.ResourceRevision.id == resource_id).\
        filter(model.ResourceRevision.expired_timestamp > now()).\
        one_or_none()

    if new_resource is not None:
        old_resource = model.Session.query(model.ResourceRevision). \
            filter(model.ResourceRevision.id == resource_id). \
            filter(model.ResourceRevision.expired_timestamp == new_resource.revision_timestamp).\
            one()
        fields = model.Resource.revisioned_fields()
        fields.remove("extras")
        for field in fields:
            old_value = getattr(old_resource, field)
            new_value = getattr(new_resource, field)
            if new_value != old_value:
                res_changes_dict[field] = {"old": old_value, "new": new_value}
        new_extras = new_resource.extras
        old_extras = old_resource.extras
        fields = new_extras.keys() + [key for key in old_extras if key not in new_extras]
        for field in fields:
            old_value = None
            new_value = None
            if field in old_extras:
                old_value = old_extras[field]
            if field in new_extras:
                new_value = new_extras[field]
            if new_value != old_value:
                res_changes_dict[field] = {"old": old_value, "new": new_value}

    return res_changes_dict


def package_get_changed_fields_after_update(pkg_dict):
    pkg_changes_dict = {}
    package_id = pkg_dict.get("id", None)

    PackageExtraRevision2 = aliased(model.PackageExtraRevision)

    pkg_extra = model.Session.query(
            model.PackageExtraRevision.package_id,
            model.PackageExtraRevision.key,
            model.PackageExtraRevision.value,
            PackageExtraRevision2.value
        ).\
        filter(model.PackageExtraRevision.package_id == package_id).\
        filter(model.PackageExtraRevision.package_id == PackageExtraRevision2.package_id).\
        filter(model.PackageExtraRevision.key == PackageExtraRevision2.key).\
        filter(model.PackageExtraRevision.expired_timestamp > now()).\
        filter(model.PackageExtraRevision.revision_timestamp.is_(None)).\
        filter(PackageExtraRevision2.expired_timestamp > now()).\
        filter(PackageExtraRevision2.revision_timestamp.isnot(None)).\
        all()

    for package_id, key, new_value, old_value in pkg_extra:
        pkg_changes_dict[key] = {"old": old_value, "new": new_value}

    new_package = model.Session.query(model.PackageRevision). \
        filter(model.PackageRevision.id == package_id).\
        filter(model.PackageRevision.expired_timestamp > now()).\
        filter(model.PackageRevision.revision_timestamp.is_(None)).\
        one_or_none()
    old_package = model.Session.query(model.PackageRevision). \
        filter(model.PackageRevision.id == package_id).\
        filter(model.PackageRevision.expired_timestamp > now()). \
        filter(model.PackageRevision.revision_timestamp.isnot(None)). \
        first()
    if not old_package:
        return
    if new_package is not None:
        fields = model.Package.revisioned_fields()
        for field in fields:
            old_value = getattr(old_package, field)
            new_value = getattr(new_package, field)
            if new_value != old_value:
                pkg_changes_dict[field] = {"old": old_value, "new": new_value}
    return pkg_changes_dict


# Task Handling (see also `put_on_a_queue` method):
# DEV-3293 required feedback from the workers for which the TaskStatus model is being used and the corresponding
# `task_status_show` and `task_status_update` API actions. General idea is to have for each package/plugin and
# resource/plugin combination a TaskStatus which contains information about the current task being pending or
# executed (so no trail).

# Create a TaskStatus when none exist yet with the default value properties `job_id` and `job_command`
def create_task(context, task_type, key, entity_type, data, job):
    task_dict = {
        "task_type": task_type,
        "key": key,
        "entity_id": get_entity_id(context, data),
        "entity_type": entity_type,
        "state": "created"
    }
    value_dict = {
        "job_id": job.id,
        "job_command": job.func_name
    }
    task_dict['value'] = json.dumps(value_dict)
    created_task = get_action_data("task_status_update", context, task_dict)
    return created_task


# Update a TaskStatus identified by task_id with a state (required), value properties and error message (optional).
# The value is a JSON stored as a string, which why the json module is involved in updating that field
def update_task(context, task_id, state, value=None, error=None):
    updated_task = None
    task = get_action_data("task_status_show", context, {"id": task_id})
    if task is not None:
        update_task_dict = {
            "id": task_id,
            "entity_id": task.get("entity_id"),
            "task_type": task.get("task_type"),
            "entity_type": task.get("entity_type"),
            "key": task.get("key"),
            "state": state,
            "error": error
        }
        if value is not None and isinstance(value, dict):
            current_value = task.get("value", None)
            if current_value:
                current_value_dict = json.loads(current_value)
                current_value_dict.update(value)
                update_task_dict['value'] = json.dumps(current_value_dict)
            else:
                update_task_dict['value'] = json.dumps(value)
        updated_task = get_action_data("task_status_update", context, update_task_dict)
    return updated_task


# Upsert a TaskStatus (update if exists and otherwise create)
def upsert_task(context, name, entity_type, data, job):
    task_dict = {
        "entity_id": get_entity_id(context, data),
        "task_type": name,
        "key": name
    }
    task = get_action_data("task_status_show", context, task_dict)
    if task is None:
        task = create_task(context, name, name, entity_type, data, job)
    else:
        value_dict = {
            "job_id": job.id,
            "job_command": job.func_name
        }
        task = update_task(context, task.get("id"), "created", value_dict, error=None)
    return task


# This should return the correct entity_id (being package_id, resource_id, whatever). Should be implemented
def get_entity_id(context, data):
    return data['id']


def donl_link_is_enabled(pkg_dict):
    donl_link_field_name = 'donl_link_enabled'
    return donl_link_field_name in pkg_dict and pkg_dict[donl_link_field_name] == 'True'


def geonetwork_link_is_enabled(pkg_dict):
    geonetwork_link_field_name = 'geonetwork_link_enabled'
    return geonetwork_link_field_name in pkg_dict and pkg_dict[geonetwork_link_field_name] == 'True'


def geoserver_link_is_enabled(pkg_dict):
    geoserver_link_field_name = 'geoserver_link_enabled'
    return geoserver_link_field_name in pkg_dict and pkg_dict[geoserver_link_field_name] == 'True'


def should_link_to_donl(pkg_dict):
    return donl_link_is_enabled(pkg_dict) and not geonetwork_link_is_enabled(pkg_dict)

def resource_has_geoserver_metadata_populated(configuration, resource):
    '''
    Check that all the geoserver related metadata exist and have values
    '''
    geoserver_resource_metadata_dict = [metadata.strip() for metadata in
                                        configuration.geoserver_resource_metadata.split(',')]
    for field in geoserver_resource_metadata_dict:
        if not field in resource.keys():
            return False
        if field in resource.keys() and not resource[field]:
            return False
    return True
