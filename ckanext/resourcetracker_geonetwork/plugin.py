import logging
import urlparse

import ckanext.resourcetracker.plugin as resourcetracker
import ckan.plugins.toolkit as toolkit
from worker.geonetwork import GeoNetworkWorkerWrapper

logging.basicConfig()
log = logging.getLogger(__name__)

class Resourcetracker_GeonetworkPlugin(resourcetracker.ResourcetrackerPlugin):

    queue_name = 'geoserver'
    worker = GeoNetworkWorkerWrapper()

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')

    def after_create(self, context, resource):
        # Do not put a task on the geonetwork queue in case of a create. This
        # should be handled by geoserver worker. 
        pass 

    def after_update(self, context, resource):
        # Do not put a task on the geonetwork queue in case of a update. This
        # should be handled by geoserver worker. 
        pass 

    def before_delete(self, context, resource, resources):
        # Do not put a task on the geonetwork queue in case of a delete. This
        # should be handled by geoserver worker. But it doesn't work in case
        # of NGR. 
        pass 

    def before_show(self, resource_dict):
        """
        see: https://docs.ckan.org/en/2.8/extensions/plugin-interfaces.html#ckan.plugins.interfaces.IResourceController.before_show
        The resource_dict is the dictionary as it would be returned as either a resource_show, a
        pacakge_show or any other api endpoint that would return resource information
        :param resource_dict:
        :return:
        """
        geonetwork_url = toolkit.config.get('ckanext.{}.geonetwork.url'.format(self.name), 'undefined')
        if geonetwork_url.find('undefined') != "-1":
            # log.info('''Connected to GeoNetwork {0}. Include in dict!'''.format(geonetwork_url))
            parameters = urlparse.urlparse(geonetwork_url)
            geonetwork_url = parameters.scheme + '://' + parameters.hostname
            if parameters.port is not None:
                geonetwork_url += ':' + str(parameters.port)
            geonetwork_url += parameters.path + '/srv/dut/catalog.search#/metadata/' + resource_dict['id']
            resource_dict["geonetwork_url"] = geonetwork_url
        # else:
        #     log.info('''Not connected to GeoNetwork ({0}). Do not include in dict.'''.format(geonetwork_url.find('undefined')))
