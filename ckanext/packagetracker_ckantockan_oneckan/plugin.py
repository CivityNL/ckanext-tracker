from ckanext.tracker.plugin import TrackerPluginException
import ckanext.packagetracker_ckantockan.plugin as packagetracker_ckantockan
from worker.ckan_to_ckan.oneckan import CkanToOneCkanWorkerWrapper
from mapper.oneckan.mapper_oneckan import MapperOneCkan
from helpers import  get_packagetracker_ckantockan_badge
import ckan.plugins as plugins
import logging

log = logging.getLogger(__name__)


class SkipEnqueueException(TrackerPluginException):
    pass


class TriggerDeleteException(TrackerPluginException):
    pass


class Packagetracker_Ckantockan_OneCkanPlugin(packagetracker_ckantockan.Packagetracker_CkantockanPlugin):
    plugins.implements(plugins.ITemplateHelpers)

    worker = CkanToOneCkanWorkerWrapper()
    mapper = MapperOneCkan()

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
            self.put_on_a_queue(context, data, self.do_delete())
            pass
        else:
            pass

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'get_packagetracker_ckantockan_badge': get_packagetracker_ckantockan_badge
        }
