import logging

import ckanext.resourcetracker.plugin as resourcetracker
import ckan.plugins.toolkit as toolkit
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
        geoserver_url = toolkit.config.get('ckanext.{}.geoserver.url'.format(self.name), 'undefined')
        if geoserver_url.find('undefined') != -1:
            # log.info('''Connected to GeoServer {0}. Include in dict!'''.format(geoserver_url))
            pretty_geoserver_url = toolkit.config.get('ckanext.{}.source_ckan_host'.format(self.name));
            if pretty_geoserver_url is not None:
                pretty_geoserver_url += '/ows?'  # will change later
                resource_dict["ows_url"] = pretty_geoserver_url
                resource_dict["wms_layer_name"] = resource_dict['id']
                resource_dict["wfs_featuretype_name"] = '@@todo-lookup-namespace' + ':' + resource_dict['id']
        # else:
        #     log.info('Not connected to GeoServer {0}. Do not include in dict.')
