import ckanext.packagetracker_ckantockan_oneckan.plugin as packagetracker_ckantockan_oneckan
from mapper.rotterdam.mapper_rotterdam import MapperRotterdam
import logging

log = logging.getLogger(__name__)


class Packagetracker_Ckantockan_OneCkan_RotterdamPlugin(packagetracker_ckantockan_oneckan.Packagetracker_Ckantockan_OneCkanPlugin):
    mapper = MapperRotterdam()
    queue_name = 'packagetracker_ckantockan_oneckan'

