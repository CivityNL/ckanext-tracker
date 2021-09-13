import logging

import ckan.model as model
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

log = logging.getLogger(__name__)


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


def is_private(pkg_dict):
    if 'private' in pkg_dict:
        return pkg_dict['private']
    return False
