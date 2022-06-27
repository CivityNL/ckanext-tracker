import logging

from ckanext.tracker_ckantockan.helpers import has_id, is_draft, link_is_enabled, is_private
from ckanext.tracker_ckantockan.plugin import CkanToCkanTrackerPlugin
from mapper.oneckan.mapper_oneckan import MapperOneCkan
from worker.ckan_to_ckan.oneckan import CkanToOneCkanWorkerWrapper

log = logging.getLogger(__name__)


class CkanToCkanOneCkanTrackerPlugin(CkanToCkanTrackerPlugin):
    """
    This tracker connects packages between one-ckan, specifically from catalogus to dataplatform based on the following
    requirements:
    - package is not private or a draft
    - the package extra field 'dataplatform_link_enabled' is set to 'True'
    """

    worker = CkanToOneCkanWorkerWrapper()
    mapper = MapperOneCkan()

    badge_title = "Dataplatform"
    ignore_resources = True

    #  Return the action for each Hook - Default to None ***********************************
    def action_to_take_on_package_create(self, context, package):
        if not has_id(package):
            log.debug("No package_id could be found, so nothing to do")
            return None
        if is_draft(package):
            log.debug('Drafts are weird. Let\'s wait until it finished before doing something')
            return None
        if is_private(package):
            log.debug('Package is private so not linking')
            return None
        if not link_is_enabled(package, 'dataplatform_link_enabled'):
            log.debug('Link is not enabled.')
            return None
        return self.get_worker().create_package

    def action_to_take_on_package_update(self, context, package, package_changes):
        if package_changes:
            # Do nothing cases
            if is_draft(package) and self.value_was('state', 'draft', package_changes):
                log.debug('Drafts are weird. Let\'s wait until it finished before doing something')
                return None
            if is_private(package) and self.value_was('private', True, package_changes):
                log.debug('Package is private so not linking')
                return None
            if not link_is_enabled(package, 'dataplatform_link_enabled') and not self.value_was('dataplatform_link_enabled', 'True', package_changes):
                log.debug('Link is not enabled.')
                return None

            # Trigger Deletion Cases FIXME issue when is draft and changes=None
            if (is_draft(package) and not self.value_was('state', 'draft', package_changes)) or \
                    (is_private(package) and not self.value_was('private', True, package_changes)) or\
                    (not link_is_enabled(package, 'dataplatform_link_enabled') and self.value_was('dataplatform_link_enabled', 'True', package_changes)):
                return self.get_worker().purge_package
        else:
            log.info('Doing Nothing because no package_changes')
            return None

        # Trigger Update Cases
        return self.get_worker().upsert_package

    def action_to_take_on_package_delete(self, context, package):
        if is_draft(package):
            log.debug('Drafts are weird. Let\'s wait until it finished before doing something')
            return None
        if is_private(package):
            log.debug('Package is private so no action needed')
            return None
        if not link_is_enabled(package, 'dataplatform_link_enabled'):
            log.debug('Link is not enabled, so no action needed.')
            return None
        return self.get_worker().purge_package

    def action_to_take_on_package_purge(self, context, package):
        return self.action_to_take_on_package_delete(context, package)

    # Helpers
    def value_was(self, key, value, changes):
        if not changes:
            return False
        # {"state": {"old": value, "new": value}}
        return key in changes and changes[key]["old"] == value
