import logging
from typing import Dict, Optional, List
from ckan.model import State

log = logging.getLogger(__name__)


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
