import logging

from ckanext.tracker_ckantockan.plugin import CkanToCkanTrackerPlugin
from helpers import should_link_to_donl
from mapper.oneckan.mapper_oneckan import MapperOneCkan
from worker.ckan_to_ckan.donl import CkanToCkanDONLWorkerWrapper
from ckanext.tracker_ckantockan.helpers import is_private, is_draft, has_id

log = logging.getLogger(__name__)


class CkanToCkanDonlTrackerPlugin(CkanToCkanTrackerPlugin):
    """
    This tracker connects packages to DONL (a.k.a https://data.overheid.nl/) which have the following requirements:
    - package is not private or a draft
    - the package extra field 'donl_link_enabled' is set to 'True'
    - the package extra field 'geonetwork_link_enabled' is NOT set to 'True'
    This latest requirement is due to the fact that DONL itself also gathers information from NGR (https://www.nationaalgeoregister.nl/)
    so sending it to both would be redundant
    """

    worker = CkanToCkanDONLWorkerWrapper()
    mapper = MapperOneCkan()

    ignore_packages = False
    ignore_resources = True
    separate_tracking = False

    badge_title = "DONL"

    def action_to_take_on_package_purge(self, context, package):
        return self.action_to_take_on_package_delete(context, package)

    def action_to_take_on_package_update(self, context, package, package_changes):
        if not has_id(package):
            log.debug("No package_id could be found, so nothing to do")
            return None
        if is_draft(package):
            log.debug('Drafts are weird. Let\'s wait until it finished before doing something')
            return None
        if not should_link_to_donl(package) or is_private(package):
            log.debug("Will try to delete any corresponding package in DONL")
            return self.get_worker().purge_package
        if package_changes:
            log.debug("Will try to create or update any corresponding package in DONL")
            return self.get_worker().upsert_package
        log.debug("No action will be taken to change any corresponding package in DONL")
        return None

    def action_to_take_on_package_create(self, context, package):
        return self.action_to_take_on_package_update(context, package, None)

    def action_to_take_on_package_delete(self, context, package):
        return self.get_worker().purge_package
