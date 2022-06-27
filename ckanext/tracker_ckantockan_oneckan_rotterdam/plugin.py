import logging

from ckanext.tracker_ckantockan_oneckan.plugin import CkanToCkanOneCkanTrackerPlugin
from mapper.rotterdam.mapper_rotterdam import MapperRotterdam

log = logging.getLogger(__name__)


class CkanToCkanOneCkanRotterdamTrackerPlugin(CkanToCkanOneCkanTrackerPlugin):
    """
    This is a specific implementation of the Packagetracker_Ckantockan_OneCkanPlugin for Rotterdam which requires a
    different mapper. The queue_name is overridden to use the same worker (otherwise it would be rotterdam specific)
    """

    mapper = MapperRotterdam()
    queue_name = 'tracker_ckantockan_oneckan'
