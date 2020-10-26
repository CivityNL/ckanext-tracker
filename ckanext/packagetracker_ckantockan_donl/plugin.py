from worker.ckan_to_ckan.donl import CkanToCkanDONLWorkerWrapper
import ckanext.packagetracker_ckantockan.plugin as packagetracker_ckantockan
from worker.ckan_to_ckan.mapper.oneckan.mapper_oneckan import MapperOneCkan
from ckanext.tracker.plugin import TrackerPluginException
import ckan.plugins.toolkit as toolkit
from helpers import is_action_done_by_worker, is_private, get_packagetracker_ckantockan_donl_badge, send_feedback
import ckan.plugins as plugins

import logging
log = logging.getLogger(__name__)


class SkipEnqueueException(TrackerPluginException):
    pass


class IsPrivateException(TrackerPluginException):
    pass


class Packagetracker_Ckantockan_DonlPlugin(packagetracker_ckantockan.Packagetracker_CkantockanPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)

    worker = CkanToCkanDONLWorkerWrapper()
    mapper = MapperOneCkan()

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

        package_id = data.get("id", None)
        if package_id is None:
            log.debug("No package_id could be found, so nothing to do")
            raise SkipEnqueueException

        if not self.should_link_to_donl(data):
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

        action = job.func_name
        if is_private(data) and action not in ('delete_package', 'purge_package'):
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

    def should_link_to_donl(self, pkg_dict):
        return self.donl_link_is_enabled(pkg_dict) and not self.geonetwork_link_is_enabled(pkg_dict)

    def donl_link_is_enabled(self, pkg_dict):
        donl_link_field_name = 'donl_link_enabled'
        return donl_link_field_name in pkg_dict and pkg_dict[donl_link_field_name] == 'True'

    def geonetwork_link_is_enabled(self, pkg_dict):
        geonetwork_link_field_name = 'geonetwork_link_enabled'
        return geonetwork_link_field_name in pkg_dict and pkg_dict[geonetwork_link_field_name] == 'True' and self.geoserver_link_is_enabled(pkg_dict)

    def geoserver_link_is_enabled(self, pkg_dict):
        geoserver_link_field_name = 'geoserver_link_enabled'
        return geoserver_link_field_name in pkg_dict and pkg_dict[geoserver_link_field_name] == 'True'
