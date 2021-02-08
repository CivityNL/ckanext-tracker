import logging

from worker.ckan_to_ckan.oneckan import CkanToOneCkanWorkerWrapper
import ckanext.resourcetracker_ckantockan.plugin as resourcetracker_ckantockan

log = logging.getLogger(__name__)


class Resourcetracker_Ckantockan_OneCkanPlugin(resourcetracker_ckantockan.Resourcetracker_CkantockanPlugin):

    queue_name = 'resourcetracker_ckantockan_oneckan'
    worker = CkanToOneCkanWorkerWrapper()

    def after_create(self, context, resource):
        log.info('after_update from {}, action: {}'.format(__name__, 'pass'))
        pass

    def after_update(self, context, resource):
        log.info('after_update from {}, action: {}'.format(__name__, 'create_datadictionary'))
        self.put_on_a_queue(context, resource, self.get_worker().create_datadictionary)

    def before_delete(self, context, resource, resources):
        log.info('after_update from {}, action: {}'.format(__name__, 'pass'))
        pass
