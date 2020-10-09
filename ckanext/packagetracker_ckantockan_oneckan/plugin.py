from worker.ckan_to_ckan.oneckan import CkanToOneCkanWorkerWrapper
import ckanext.packagetracker_ckantockan.plugin as packagetracker_ckantockan
from worker.ckan_to_ckan.mapper.oneckan.mapper_oneckan import MapperOneCkan
from ckanext.tracker.plugin import TrackerPluginException


class SkipEnqueueException(TrackerPluginException):
    pass


class Packagetracker_Ckantockan_OneCkanPlugin(packagetracker_ckantockan.Packagetracker_CkantockanPlugin):
    worker = CkanToOneCkanWorkerWrapper()
    mapper = MapperOneCkan()

    def do_update(self):
        return self.do_upsert()

    def before_enqueue(self, context, data, job):
        if not self.should_enqueue(data):
            raise SkipEnqueueException

    def handle_error(self, context, data, command, error):
        if isinstance(error, SkipEnqueueException):
            self.put_on_a_queue(context, data, self.do_delete())

    def should_enqueue(self, data):
        return 'access_rights' in data and data.get('access_rights') == "http://publications.europa.eu/resource/authority/access-right/PUBLIC"
