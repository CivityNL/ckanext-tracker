import logging

from ckanext.tracker_ckantockan_oneckan.plugin import CkanToCkanOneCkanTrackerPlugin
from mapper.lidingo.mapper_lidingo import MapperLidingo

log = logging.getLogger(__name__)


class CkanToCkanOneCkanLidingoTrackerPlugin(CkanToCkanOneCkanTrackerPlugin):
    """
    This is a specific implementation of the Packagetracker_Ckantockan_OneCkanPlugin for Rotterdam which requires a
    different mapper. The queue_name is overridden to use the same worker (otherwise it would be rotterdam specific)
    """

    mapper = MapperLidingo()
    queue_name = 'tracker_ckantockan_oneckan'
