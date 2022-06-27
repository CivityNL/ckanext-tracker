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

    badge_title = "DONL"

    def do_package_update(self):
        return self.do_package_upsert()

    def action_to_take_on_package_purge(self, context, package):
        return True

    def action_to_take_on_package_update(self, context, package, package_changes):
        if not has_id(package):
            log.debug("No package_id could be found, so nothing to do")
            return False
        if is_draft(package):
            log.debug('Drafts are weird. Let\'s wait until it finished before doing something')
            return False
        if not should_link_to_donl(package):
            return False
        if is_private(package):
            return self.put_on_a_queue(context, 'package', self.do_package_delete(), None, package, None, package_changes)
        return True

    def action_to_take_on_package_create(self, context, package):
        return self.action_to_take_on_package_update(context, package, None)

    def action_to_take_on_package_delete(self, context, package):
        return True
