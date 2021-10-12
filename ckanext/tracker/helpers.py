import json
import logging

import ckan.plugins.toolkit as toolkit
from ckanext.tracker.backend import TrackerBackend

log = logging.getLogger(__name__)


def get_tracker_status(context, tracker, entity_id):
    """
    This method will return the TaskStatus information for a specific tracker and entity_id
    @param context: context
    @param tracker: TrackerModel
    @param entity_id: the id of an entity (resource id, package id, etc)
    @return: dict containing the information of the specific TaskStatus object
    """
    if not entity_id:
        return None
    data_dict = {
        'entity_id': entity_id,
        'task_type': tracker.name,
        'key': tracker.name
    }
    task_dict = {}
    try:
        task_dict = toolkit.get_action('task_status_show')(context, data_dict)
        if 'value' in task_dict and task_dict.get('value') is not None:
            task_dict['value'] = json.loads(task_dict.get('value'))
    except Exception as e:
        return None
    return task_dict


def get_tracker_statuses(entity_type, entity_id):
    """
    This method will get all trackers registered using the entity_type from the backend and if those are configured to
    show the UI it will get the specific TaskStatus information
    @param entity_type: type of tracker ('resource', 'package', etc)
    @param entity_id: the id of an entity (resource id, package id, etc)
    @return: list of dicts containing the information of the TaskStatus objects
    """
    context = {'user': toolkit.c.user}
    statuses = []
    for tracker in TrackerBackend.get_trackers_by_type(entity_type):
        if tracker.show_ui_method(context, tracker.type, entity_id):
            status = get_tracker_status(context, tracker, entity_id)
            if status is not None:
                statuses.append(status)
    return statuses


def get_tracker_badges(entity_type, entity_id):
    """
    This method will get all trackers registered using the entity_type from the backend and if those are configured to
    show the badge it will get the specific badge
    @param entity_type: type of tracker ('resource', 'package', etc)
    @param entity_id: the id of an entity (resource id, package id, etc)
    @return: list of strings containing the badges
    """
    context = {'user': toolkit.c.user}
    badges = []
    for tracker in TrackerBackend.get_trackers_by_type(entity_type):
        if tracker.show_badge_method(context, tracker.type, entity_id):
            badge = get_tracker_badge(context, tracker, entity_id)
            if badge is not None:
                badges.append(badge)
    return badges


def get_tracker_badge(context, tracker, entity_id):
    """
    This method will return the badge for a specific tracker and entity_id
    @param context: context
    @param tracker: TrackerModel
    @param entity_id: the id of an entity (resource id, package id, etc)
    @return: string containing the code of the badge
    """
    task_dict = get_tracker_status(context, tracker, entity_id)
    if task_dict is None:
        return None

    state = task_dict.get('state', 'error')
    status = state
    if state == 'error':
        color = '#e05d44'
    elif state == 'complete':
        color = '#97CA00'
    else:
        color = '#9f9f9f'
    # h.flash_success('Bladiebla')
    return create_badge(tracker.name, color, tracker.badge_title_method(), status)


def create_badge(identifier, color, title, status):
    """
    This method will create the svg as a string to be shown in HTML. It will try to calculate the width of all the
    separate elements (title, status) based on the strings
    @param identifier: to distinguish this particular badge which should always be different
    @param color: hex representation of the color
    @param title: title to be shown (left side of the badge)
    @param status: status to be shown (right side of the badge)
    @return: string containing the svg code
    """

    status = toolkit._(status)
    title_width = calculate_length_text_in_pixels(title, 11)
    status_width = calculate_length_text_in_pixels(status, 11)

    return '''
    <svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20">
        <linearGradient id="b-{identifier}" x2="0" y2="100%">
            <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
            <stop offset="1" stop-opacity=".1"/>
        </linearGradient>
        <clipPath id="a-{identifier}">
            <rect width="{width}" height="20" rx="3" fill="#fff"/>
        </clipPath>
        <g clip-path="url(#a-{identifier})">
            <path fill="#555" d="M0 0h{title_width}v20H0z"/>
            <path fill="{color}" d="M{title_width} 0h{status_width}v20H{title_width}z"/>
            <path fill="url(#b-{identifier})" d="M0 0h{width}v20H0z"/>
        </g>
        <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11px">
            <text x="{title_mid}" y="15" fill="#010101" fill-opacity=".3">{title}</text>
            <text x="{title_mid}" y="14">{title}</text>
            <text x="{status_mid}" y="15" fill="#010101" fill-opacity=".3">{status}</text>
            <text x="{status_mid}" y="14">{status}</text>
        </g>
    </svg>
    '''.format(
        identifier=identifier,
        width=title_width+status_width,
        title_width=title_width, status_width=status_width,
        title_mid=title_width/2, status_mid=title_width + status_width/2,
        color=color, title=title, status=status)


def calculate_length_text_in_pixels(text, font_size):
    """
    Simple first try to calculate the width of a text based on font size and type of characters
    """
    upper_case = sum(1 for c in text if c.isupper())
    lower_case = sum(1 for c in text if c.islower())
    unknown_case = len(text) - (upper_case + lower_case)
    return font_size*unknown_case + (font_size+1)*upper_case + (font_size-1)*lower_case
