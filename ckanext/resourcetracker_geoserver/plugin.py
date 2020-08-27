import logging

import ckanext.resourcetracker.plugin as resourcetracker
from worker.geoserver import GeoServerWorkerWrapper

logging.basicConfig()
log = logging.getLogger(__name__)

class Resourcetracker_GeoserverPlugin(resourcetracker.ResourcetrackerPlugin):

    queue_name = 'geoserver'
    worker = GeoServerWorkerWrapper()

    def after_create(self, context, resource):
        log.info('after_create from {}, action: {}'.format(__name__, 'none'))
        # Do not put a task on the geoserver queue in case of a create. Create 
        # should be handled by datastoretracker_geoserver. 

    def before_show(self, resource_dict):
        """
        see: https://docs.ckan.org/en/2.8/extensions/plugin-interfaces.html#ckan.plugins.interfaces.IResourceController.before_show
        The resource_dict is the dictionary as it would be returned as either a resource_show, a
        pacakge_show or any other api endpoint that would return resource information
        :param resource_dict:
        :return:
        """
        log.info('before_show from {}, action: {}'.format(__name__, 'none'))
        resource_dict["Bas"] = 'Vanmeulebrouk'
