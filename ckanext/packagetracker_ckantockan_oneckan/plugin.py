import logging

import ckanext.packagetracker_ckantockan.plugin as packagetracker_ckantockan
from ckanext.tracker.classes.base_tracker import TrackerPluginException
from mapper.oneckan.mapper_oneckan import MapperOneCkan
from worker.ckan_to_ckan.oneckan import CkanToOneCkanWorkerWrapper

log = logging.getLogger(__name__)


class SkipEnqueueException(TrackerPluginException):
    pass


class TriggerDeleteException(TrackerPluginException):
    pass


class Packagetracker_Ckantockan_OneCkanPlugin(packagetracker_ckantockan.Packagetracker_CkantockanPlugin):
    """
    This tracker connects packages between one-ckan, specifically from catalogus to dataplatform based on the following
    requirements:
    - package is not private or a draft
    - the package extra field 'dataplatform_link_enabled' is set to 'True'
    """

    worker = CkanToOneCkanWorkerWrapper()
    mapper = MapperOneCkan()

    badge_title = "Dataplatform"

    def do_update(self):
        return self.do_upsert()

    def before_enqueue(self, context, data, job):
        # This function checks for conditions to avoid enqueue. Throws different exceptions for each case.
        package_id = data.get("id", None)
        is_draft = 'state' in data and data["state"] == 'draft'
        if not package_id or is_draft:
            if not package_id:
                log.debug("No package_id could be found, so nothing to do")
            else:
                log.debug('Drafts are weird. Let\'s wait until it finished before doing something')
            raise SkipEnqueueException

        is_dp_link_enabled = 'dataplatform_link_enabled' in data and data.get('dataplatform_link_enabled') == "True"
        is_private = ('private' in data and data['private'])
        action_is_not_delete = job.func_name not in ('delete_package', 'purge_package')
        if (not is_dp_link_enabled or is_private) and action_is_not_delete:
            log.debug('Link should not be in place. Triggering Removal.')
            raise TriggerDeleteException

    def handle_error(self, context, data, command, error):
        if isinstance(error, SkipEnqueueException):
            pass
        elif isinstance(error, TriggerDeleteException):
            self.put_package_on_a_queue(context, data, self.do_delete())
            pass
        else:
            pass

    def show_badge_for_package_type(self, context, package_dict):
        is_draft = 'state' in package_dict and package_dict["state"] == 'draft'
        is_dp_link_enabled = 'dataplatform_link_enabled' in package_dict and package_dict.get('dataplatform_link_enabled') == "True"
        is_private = ('private' in package_dict and package_dict['private'])
        return not is_draft and is_dp_link_enabled and not is_private
