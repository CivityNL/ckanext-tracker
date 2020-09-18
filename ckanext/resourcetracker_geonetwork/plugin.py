import logging
import urlparse

import ckanext.resourcetracker.plugin as resourcetracker
import ckan.plugins.toolkit as toolkit
from worker.geonetwork import GeoNetworkWorkerWrapper
from domain import Configuration
from worker.geonetwork.rest import GeoNetworkRestApi

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
            log.info('''Connected to GeoNetwork {0}, datastore active {1}, find {2}. Include in dict!'''.format(
                geonetwork_url, resource_dict['datastore_active'], geonetwork_url.find('undefined')
            ))

            if resource_dict['datastore_active']:
                configuration = Configuration.from_dict(self.get_configuration_dict())

                api = GeoNetworkRestApi(configuration)

                record = api.read_record(resource_dict['id'])

                if record is not None:
                    parameters = urlparse.urlparse(geonetwork_url)
                    output_url = parameters.scheme + '://' + parameters.hostname
                    if parameters.port is not None:
                        output_url += ':' + str(parameters.port)
                    output_url += parameters.path + '/srv/dut/catalog.search#/metadata/' + resource_dict['id']
                    resource_dict["geonetwork_url"] = output_url
                else:
                    log.info('''Record not found. Do not include in dict.''')
                    resource_dict["geonetwork_url"] = None
            else:
                log.info('''Datastore active ({0}). Do not include in dict.'''.format(resource_dict['datastore_active']))
                resource_dict["geonetwork_url"] = None
        else:
            log.info('''Not connected to GeoNetwork ({0}). Do not include in dict.'''.format(geonetwork_url.find('undefined')))
            resource_dict["geonetwork_url"] = None
