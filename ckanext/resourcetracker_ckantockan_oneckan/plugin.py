import logging

import ckanext.resourcetracker_ckantockan.plugin as resourcetracker_ckantockan
from worker.ckan_to_ckan.oneckan import CkanToOneCkanWorkerWrapper

log = logging.getLogger(__name__)


# IS THIS TRACKER EVEN USED/ACTIVE
class Resourcetracker_Ckantockan_OneCkanPlugin(resourcetracker_ckantockan.Resourcetracker_CkantockanPlugin):
    """No idea what the use is of this Tracker. If you know please add it here"""

    queue_name = 'resourcetracker_ckantockan_oneckan'
    worker = CkanToOneCkanWorkerWrapper()

    def after_create(self, context, resource):
        log.info('after_create from {}, action: {}'.format(__name__, 'pass'))
        pass

    def after_update(self, context, resource):
        log.info('after_update from {}, action: {}'.format(__name__, 'create_datadictionary'))
        self.put_resource_on_a_queue(context, resource, self.get_worker().create_datadictionary)

    def before_delete(self, context, resource, resources):
        log.info('before_delete from {}, action: {}'.format(__name__, 'pass'))
        pass
