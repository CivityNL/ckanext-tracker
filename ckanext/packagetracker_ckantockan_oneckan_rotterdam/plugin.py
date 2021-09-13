import logging

import ckanext.packagetracker_ckantockan_oneckan.plugin as packagetracker_ckantockan_oneckan
from mapper.rotterdam.mapper_rotterdam import MapperRotterdam

log = logging.getLogger(__name__)


class Packagetracker_Ckantockan_OneCkan_RotterdamPlugin(packagetracker_ckantockan_oneckan.Packagetracker_Ckantockan_OneCkanPlugin):
    """
    This is a specific implementation of the Packagetracker_Ckantockan_OneCkanPlugin for Rotterdam which requires a
    different mapper. The queue_name is overridden to use the same worker (otherwise it would be rotterdam specific)
    """

    mapper = MapperRotterdam()
    queue_name = 'packagetracker_ckantockan_oneckan'
