import ckan.plugins.toolkit as toolkit
import ckan.model as model
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import logging
log = logging.getLogger(__name__)


def is_sync_user(context, configuration):
    return context['user'] == configuration.source_ckan_user


def is_action_done_by_worker(context, pkg_dict, configuration):
    """
    This method will check if the latest package update contains any updated values for one of the configuration fields,
    because those will only be set by the extensions or the workers
    :param context:
    :param pkg_dict:
    :param configuration:
    :return: Either True if this updates was indeed caused by a worker/extension, otherwise False
    """

    options = [configuration.source_job_status_field, configuration.source_job_id_field]
    revision_id = pkg_dict.get('revision_id', None)
    if revision_id is None:
        return False

    try:
        updated_package_extras = get_updated_package_extras(revision_id)
    except ValueError as error:
        log.error("Something went wrong when getting the updated_package_extras", error)
        return True

    if len(updated_package_extras) > 2 or len(updated_package_extras) == 0:
        return False
    else:
        for result in updated_package_extras:
            if result.key not in options:
                return False
    return True


def get_updated_package_extras(revision_id):
    """
    This elaborate method gets the latest updated PackageExtra objects. The logic is based on the fact that either the
    PackageExtra where updated together with the Package and as such will have the same timestamp (and nothing newer).
    Or in the case that only PackageExtra objects where updated it will return the last updated objects.
    :param revision_id: revision ID of the package
    :return: array of updated PackageExtra objects (can be an empty array)
    """
    # check if the revision_id is not None
    if revision_id is None:
        raise ValueError("Revision_id needs to have a value!")

    # try to get the PackageRevision with the revision_id
    try:
        revision = model.Session.query(model.PackageRevision).\
            filter(model.PackageRevision.revision_id == revision_id).one()
    except NoResultFound:
        raise ValueError("No revision found for revision_id = '{}'".format(revision_id))
    except MultipleResultsFound:
        raise ValueError("Multiple revisions found for revision_id = '{}'".format(revision_id))

    # check if any PackageExtra where updated after this revision and select the latest timestamp
    max_package_extra_revision_timestamp = model.Session.query(func.max(model.PackageExtraRevision.expired_timestamp)).\
        filter(model.PackageExtraRevision.package_id == revision.id).\
        filter(model.PackageExtraRevision.expired_timestamp >= revision.metadata_modified)
    # retrieve all the PackageExtra with this timestamp
    updated_package_extras = model.Session.query(model.PackageExtraRevision).\
        filter(model.PackageExtraRevision.package_id == revision.id).\
        filter(model.PackageExtraRevision.expired_timestamp == max_package_extra_revision_timestamp).all()

    return updated_package_extras


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
