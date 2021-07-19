import ckanext.packagetracker_ckantockan_oneckan.plugin as packagetracker_ckantockan_oneckan
from mapper.rotterdam.mapper_rotterdam import MapperRotterdam
from helpers import  get_packagetracker_ckantockan_badge
import logging

log = logging.getLogger(__name__)


class Packagetracker_Ckantockan_OneCkan_RotterdamPlugin(packagetracker_ckantockan_oneckan.Packagetracker_Ckantockan_OneCkanPlugin):
    mapper = MapperRotterdam()
    queue_name = 'packagetracker_ckantockan_oneckan'

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'get_packagetracker_ckantockan_badge': get_packagetracker_ckantockan_badge
        }
