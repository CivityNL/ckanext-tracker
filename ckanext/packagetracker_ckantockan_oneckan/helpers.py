import ckan.plugins.toolkit as toolkit
import ckan.model as model
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import logging

log = logging.getLogger(__name__)


def get_packagetracker_ckantockan_badge(pkg_dict):
    package_id = pkg_dict.get('id', None)
    if not package_id:
        return ''
    data_dict = {'entity_id': package_id,
                 'task_type': 'packagetracker_ckantockan_oneckan',
                 'key': 'packagetracker_ckantockan_oneckan'}
    try:
        task_dict = toolkit.get_action('task_status_show')({}, data_dict)
    except Exception as e:
        return ''
    state = task_dict.get('state', 'error')
    text = state
    if state == 'error':
        color = '#e05d44'
    elif state == 'complete':
        color = '#97CA00'
    else:
        color = '#9f9f9f'
    return create_badge(color, text)


def create_badge(color, text):
    return '''
    <svg xmlns="http://www.w3.org/2000/svg" width="200" height="20">
        <linearGradient id="b" x2="0" y2="100%">
            <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
            <stop offset="1" stop-opacity=".1"/>
        </linearGradient>
        <clipPath id="a">
            <rect width="200" height="20" rx="3" fill="#fff"/>
        </clipPath>
        <g clip-path="url(#a)">
            <path fill="#555" d="M0 0h100v20H0z"/>
            <path fill="{color}" d="M100 0h100v20H100z"/>
            <path fill="url(#b)" d="M0 0h200v20H0z"/>
        </g>
        <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
            <text x="50" y="15" fill="#010101" fill-opacity=".3">Dataplatform</text>
            <text x="50" y="14">Dataplatform</text>
            <text x="150" y="15" fill="#010101" fill-opacity=".3">{text}</text>
            <text x="150" y="14">{text}</text>
        </g>
    </svg>
    '''.format(color=color, text=text)
