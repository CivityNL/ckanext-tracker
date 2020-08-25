from worker.ckan_to_ckan.donl import CkanToCkanDONLWorkerWrapper
import ckanext.packagetracker_ckantockan.plugin as packagetracker_ckantockan
from worker.ckan_to_ckan.mapper.dataplatform.mapper_dataplatform import MapperDataplatform
from ckanext.tracker.plugin import TrackerPluginException
import ckan.plugins.toolkit as toolkit
from helpers import is_sync_user, is_private, get_packagetracker_ckantockan_donl_badge, send_feedback
import ckan.plugins as plugins

import logging
log = logging.getLogger(__name__)


class SkipEnqueueException(TrackerPluginException):
    pass


class IsPrivateException(TrackerPluginException):
    pass


class OnCreateException(TrackerPluginException):
    pass


class Packagetracker_Ckantockan_DonlPlugin(packagetracker_ckantockan.Packagetracker_CkantockanPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)

    worker = CkanToCkanDONLWorkerWrapper()
    mapper = MapperDataplatform()

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'get_packagetracker_ckantockan_donl_badge': get_packagetracker_ckantockan_donl_badge
        }

    def do_update(self):
        return self.do_upsert()

    def before_enqueue(self, context, data, job):
        configuration = self.get_configuration()
        if is_sync_user(context, configuration):
            raise SkipEnqueueException

        action = job.func_name
        # log.debug('STATUS === {}'.format(data["state"]))
        if 'state' in data and data["state"] == 'draft':
            pass
        elif is_private(data) and action not in ('delete_package', 'purge_package'):
            raise IsPrivateException
        else:
            send_feedback(configuration, data, job)

    def handle_error(self, context, data, command, error):
        if isinstance(error, SkipEnqueueException):
            pass
        elif isinstance(error, IsPrivateException):
            self.put_on_a_queue(context, data, self.do_delete())
            pass
        else:
            pass

