import logging

import ckanext.resourcetracker.plugin as resourcetracker
import ckan.plugins.toolkit as toolkit
from worker.geoserver import GeoServerWorkerWrapper
import ckan.plugins as plugins
from helpers import get_resourcetracker_geoserver_wfs, get_resourcetracker_geoserver_wms
from domain import Configuration
from worker.geoserver.rest import GeoServerRestApi

logging.basicConfig()
log = logging.getLogger(__name__)


class Resourcetracker_GeoserverPlugin(resourcetracker.ResourcetrackerPlugin):
    plugins.implements(plugins.ITemplateHelpers)

    queue_name = 'geoserver'
    worker = GeoServerWorkerWrapper()

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'get_resourcetracker_geoserver_wfs': get_resourcetracker_geoserver_wfs,
            'get_resourcetracker_geoserver_wms': get_resourcetracker_geoserver_wms
        }

    # IResourceController

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
        if geoserver_url.find('undefined') < 0:
            log.info('''Connected to geoserver {0}, datastore active {1}, find {2}. Investigate further.'''.format(
                geoserver_url, resource_dict['datastore_active'], geoserver_url.find('undefined')
            ))

            if resource_dict['datastore_active']:
                configuration = Configuration.from_dict(self.get_configuration_dict())

                api = GeoServerRestApi(configuration)

                workspace = api.read_workspace(configuration.workspace_name)
                if workspace is not None:
                    data_store = api.read_data_store(workspace, configuration.data_store_name)
                    if data_store is not None:
                        feature_type = api.read_feature_type(workspace, data_store, resource_dict['id'])
                        if feature_type is not None:
                            output_url = toolkit.config.get('ckanext.{}.source_ckan_host'.format(self.name))
                            output_url += '/ows?'
                            self.set_dict_elements(resource_dict, output_url, configuration.workspace_name + ':' + resource_dict['id'], configuration.workspace_name + ':' + resource_dict['id'])
                        else:
                            log.info('''Feature type not found. Do not include in dict.''')
                            self.set_dict_elements(resource_dict, None, None, None)
                    else:
                        log.info('''Data store not found. Do not include in dict.''')
                        self.set_dict_elements(resource_dict, None, None, None)
                else:
                    log.info('''Workspace not found. Do not include in dict.''')
                    self.set_dict_elements(resource_dict, None, None, None)
            else:
                log.info('''Datastore active {0}. Do not include in dict.'''.format(resource_dict['datastore_active']))
                self.set_dict_elements(resource_dict, None, None, None)
        else:
            log.info('''Not connected to geoserver ({0}). Do not include in dict.'''.format(geoserver_url.find('undefined')))
            self.set_dict_elements(resource_dict, None, None, None)
    
    def set_dict_elements(self, resource_dict, ows_url, layer_name, feature_type_name):
        resource_dict["ows_url"] = ows_url
        resource_dict["wms_layer_name"] = layer_name
        resource_dict["wfs_featuretype_name"] = feature_type_name

