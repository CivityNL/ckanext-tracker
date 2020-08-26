import ckan.plugins.toolkit as toolkit

import logging
log = logging.getLogger(__name__)


def is_sync_user(context, configuration):
    return context['user'] == configuration.source_ckan_user


def send_feedback(configuration, pkg_dict, job):
    if 'name' in pkg_dict:
        toolkit.get_action("package_patch")(
            {'user': configuration.source_ckan_user},
            {'id': pkg_dict["name"],
             configuration.source_job_status_field: 100,
             configuration.source_job_id_field: job.id})
    pass


def is_private(pkg_dict):
    if 'private' in pkg_dict:
        return pkg_dict['private']
    return False


def get_packagetracker_ckantockan_donl_badge(pkg_dict):
    if not pkg_dict['packagetracker_ckantockan_donl_status']:
        return ''
    status = int(pkg_dict['packagetracker_ckantockan_donl_status'])
    if status < 200:
        color = '#9f9f9f'
        text = 'enqueued'
    elif status < 300:
        color = '#97CA00'
        text = 'success'
    else:
        color = '#e05d44'
        text = 'failure'
    return create_badge(color, text)


def create_badge(color, text):
    return '''
    <svg xmlns="http://www.w3.org/2000/svg" width="130" height="20">
        <linearGradient id="b" x2="0" y2="100%">
            <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
            <stop offset="1" stop-opacity=".1"/>
        </linearGradient>
        <clipPath id="a">
            <rect width="130" height="20" rx="3" fill="#fff"/>
        </clipPath>
        <g clip-path="url(#a)">
            <path fill="#555" d="M0 0h50v20H0z"/>
            <path fill="{color}" d="M50 0h80v20H50z"/>
            <path fill="url(#b)" d="M0 0h130v20H0z"/>
        </g>
        <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
            <text x="25" y="15" fill="#010101" fill-opacity=".3">DONL</text>
            <text x="25" y="14">DONL</text>
            <text x="90" y="15" fill="#010101" fill-opacity=".3">{text}</text>
            <text x="90" y="14">{text}</text>
        </g>
    </svg>
    '''.format(color=color, text=text)
