import logging
import ckan.model as model
from sqlalchemy.sql.expression import nullslast

log = logging.getLogger(__name__)


def get_revision_id(context):
    result = None
    revision = model.Session.query(model.Revision). \
        filter(model.Revision.author == context.get("user")). \
        order_by(model.Revision.timestamp.desc()). \
        first()
    if revision is not None:
        result = revision.id
    return result


def get_revision_model_changes(revision_model, revision_id, model_id):

    new_revision_model = None
    old_revision_model = None
    if revision_id is not None:
        # find the ResourceRevision belonging to this Revision (if it exists)
        new_revision_model = model.Session.query(revision_model). \
            filter(revision_model.id == model_id). \
            filter(revision_model.revision_id == revision_id). \
            one_or_none()

    if new_revision_model is not None:
        old_revision_model = model.Session.query(revision_model). \
                filter(revision_model.id == model_id). \
                filter(revision_model.revision_id != revision_id). \
                order_by(nullslast(revision_model.revision_timestamp.desc())). \
                first()

    return old_revision_model, new_revision_model


# { fieldname: {old: old_value, new: new_value}, ... }
def get_resource_changes(revision_id, resource_id):

    old_resource, new_resource = get_revision_model_changes(model.ResourceRevision, revision_id, resource_id)
    resource_changes_dict = get_resource_changes_dict(old_resource, new_resource)
    return resource_changes_dict


def get_resource_changes_dict(old_resource, new_resource):
    # type: (model.ResourceRevision, model.ResourceRevision) -> dict
    resource_changes_dict = {}
    if old_resource is not None and new_resource is not None:
        fields = model.Resource.revisioned_fields()
        fields.remove("last_modified")
        fields.remove("extras")
        for field in fields:
            old_value = getattr(old_resource, field)
            new_value = getattr(new_resource, field)
            if new_value != old_value:
                resource_changes_dict[field] = {"old": old_value, "new": new_value}
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
                resource_changes_dict[field] = {"old": old_value, "new": new_value}
    return resource_changes_dict


def get_package_resources_changes_dict(revision_id, package_id):
    package_resources_changes_dict = {}

    resources = model.Session.query(model.Resource). \
        filter(model.Resource.package_id == package_id). \
        all()

    for resource in resources:
        old_resource, new_resource = get_revision_model_changes(model.ResourceRevision, revision_id, resource.id)
        resource_changes_dict = get_resource_changes_dict(old_resource, new_resource)
        if resource_changes_dict:
            package_resources_changes_dict[resource.id] = resource_changes_dict

    return package_resources_changes_dict


def get_package_changes(revision_id, package_id, include_extras=True, include_resources=False):
    package_changes_dict = {}

    old_package, new_package = get_revision_model_changes(model.PackageRevision, revision_id, package_id)
    package_changes_dict = get_package_changes_dict(old_package, new_package)

    if include_extras:
        package_extra_changes_dict = get_package_extra_changes_dict(revision_id, package_id)
        package_changes_dict.update(package_extra_changes_dict)

    if include_resources:
        package_resources_changes_dict = get_package_resources_changes_dict(revision_id, package_id)
        return package_changes_dict, package_resources_changes_dict

    return package_changes_dict


def get_package_changes_dict(old_package, new_package):
    # type: (model.PackageRevision, model.PackageRevision) -> dict
    package_changes_dict = {}
    if old_package is not None and new_package is not None:
        fields = model.Package.revisioned_fields()
        fields.remove("metadata_modified")
        for field in fields:
            old_value = getattr(old_package, field)
            new_value = getattr(new_package, field)
            if new_value != old_value:
                package_changes_dict[field] = {"old": old_value, "new": new_value}
    return package_changes_dict


def get_package_extra_changes_dict(revision_id, package_id):
    package_extra_changes_dict = {}

    if revision_id is not None:

        new_package_extras = model.Session.query(
            model.PackageExtraRevision.key,
            model.PackageExtraRevision.value
        ). \
            filter(model.PackageExtraRevision.package_id == package_id). \
            filter(model.PackageExtraRevision.revision_id == revision_id). \
            order_by(model.PackageExtraRevision.key). \
            subquery()

        old_package_extras = model.Session.query(
            model.PackageExtraRevision.key,
            model.PackageExtraRevision.value
        ). \
            filter(model.PackageExtraRevision.package_id == package_id). \
            filter(model.PackageExtraRevision.revision_id != revision_id). \
            order_by(model.PackageExtraRevision.key, nullslast(model.PackageExtraRevision.revision_timestamp.desc())). \
            distinct(model.PackageExtraRevision.key). \
            subquery()

        package_extras_changes = model.Session.query(
            new_package_extras.c.key,
            new_package_extras.c.value.label("new"),
            old_package_extras.c.value.label("old")
        ). \
            filter(new_package_extras.c.key == old_package_extras.c.key). \
            all()

        for key, new, old in package_extras_changes:
            package_extra_changes_dict[key] = {"new": new, "old": old}

    return package_extra_changes_dict


def filter_fields_from_changes(changes, include_fields=None, exclude_fields=None):
    result = {}
    if include_fields is not None:
        for include_field in include_fields:
            if include_field in changes:
                log.info("Keeping field {} from changes".format(include_field))
                result[include_field] = changes[include_field]
    else:
        for field in changes:
            result[field] = changes[field]

    if exclude_fields is not None:
        for exclude_field in exclude_fields:
            if exclude_field in result:
                log.info("Removing field {} from changes".format(exclude_field))
                del result[exclude_field]

    return result