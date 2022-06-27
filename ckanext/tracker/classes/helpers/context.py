import re
from redis import Redis
import logging
import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as toolkit

log = logging.getLogger(__name__)


def init_package_context():
    return {
        'via_resource_controller': False,
        'resources': {
            'insert': [],
            'update': []
        }
    }


def add_resource_to_tracker_context(tracker_context, type, instance):
    if type in ['insert', 'update']:
        res_dict = instance.as_dict()
        res_dict["revision_id"] = instance.revision_id
        res_dict["state"] = instance.state
        tracker_context['resources'][type].append(res_dict)


def filter_updated_resources_based_on_revision(tracker_context, revision_id):
    tracker_context['resources']['update'] = [res for res in tracker_context['resources']['update'] if res['revision_id'] == revision_id]
