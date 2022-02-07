import logging

import ckan.plugins.toolkit as toolkit
import ckanext.packagetracker_ckantockan.plugin as packagetracker_ckantockan
from ckanext.tracker.classes.base_tracker import TrackerPluginException
from helpers import is_action_done_by_worker, is_private
from mapper.oneckan.mapper_oneckan import MapperOneCkan
from worker.ckan_to_ckan.donl import CkanToCkanDONLWorkerWrapper
import ckanext.tracker.classes.helpers as tracker_helpers

log = logging.getLogger(__name__)


class SkipEnqueueException(TrackerPluginException):
    pass


class IsPrivateException(TrackerPluginException):
    pass


class Packagetracker_Ckantockan_DonlPlugin(packagetracker_ckantockan.Packagetracker_CkantockanPlugin):
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

    def do_update(self):
        return self.do_upsert()

    def before_enqueue(self, context, data, job):
        package_id = data.get("id", None)
        action = job.func_name
        if package_id is None:
            log.debug("No package_id could be found, so nothing to do")
            raise SkipEnqueueException

        if not tracker_helpers.should_link_to_donl(data) and action not in ('delete_package', 'purge_package'):
            log.debug('Skipping DONL Link because it SHOULD NOT do it')
            raise SkipEnqueueException

        # the data passed does not contain the revision_id so we need to check that
        pkg_dict = toolkit.get_action("package_show")(context, {'id': package_id})

        if 'state' in pkg_dict and pkg_dict["state"] == 'draft':
            log.debug('Drafts are weird. Let\'s wait until it finished before doing something')
            raise SkipEnqueueException

        configuration = self.get_configuration()
        if is_action_done_by_worker(context, pkg_dict, configuration):
            log.debug("This action has been done by a worker or extension and will not be enqueued")
            raise SkipEnqueueException

        if is_private(data) and action not in ('delete_package', 'purge_package'):
            raise IsPrivateException

    def handle_error(self, context, data, command, error):
        if isinstance(error, SkipEnqueueException):
            pass
        elif isinstance(error, IsPrivateException):
            self.put_package_on_a_queue(context, data, self.do_delete())
            pass
        else:
            pass

    def show_badge_for_package_type(self, context, package_dict):
        is_private = 'state' in package_dict and package_dict["state"] == 'draft'
        return tracker_helpers.should_link_to_donl(package_dict) and not is_private
