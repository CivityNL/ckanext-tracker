from worker.ogr import OgrWorkerWrapper
import ckanext.resourcetracker.plugin as resourcetracker
import ckan.plugins.toolkit as toolkit
import helpers as h
from domain import Configuration
import ckan.plugins as plugins
from worker.geoserver.rest import GeoServerRestApi
import logging
logging.basicConfig()
log = logging.getLogger(__name__)

class Resourcetracker_OgrPlugin(resourcetracker.ResourcetrackerPlugin):
    plugins.implements(plugins.ITemplateHelpers)

    queue_name = 'ogr'
    worker = OgrWorkerWrapper()
    resource_metadata_changed = False

    def after_create(self, context, resource):
        log.debug('OGR: after_create')
        # stop datastore_create call from re-triggering ogr-worker
        if resource.get("url_type") != 'datastore' and "_datastore_only_resource" not in resource.get("url"):
            self.put_on_a_queue(context, resource, self.get_worker().create_resource)

    def before_update(self, context, current, resource):
        # Catch resource.name change so we can update it on geoserver side
        if current.get('name') != resource.get('name'):
            log.debug('OGR: before_update *metadata values have changed*')
            self.resource_metadata_changed = True

    def after_update(self, context, resource):
        log.debug('OGR: after_update')
        if resource.get("url_type") != 'datastore':
            self.put_on_a_queue(context, resource, self.get_worker().update_resource)
        else:
            if self.resource_metadata_changed:
                # Trigger geoserver update_feature_type only
                from worker.geoserver import GeoServerWorkerWrapper
                self.queue_name = 'geoserver'
                self.worker = GeoServerWorkerWrapper()
                self.put_on_a_queue(context, resource, self.get_worker().update_resource)
        #TODO2 if resource.get("url_type") == 'datastore':

    def before_delete(self, context, resource, resources):
        log.debug('OGR: before_delete')
        self.put_on_a_queue(context, resource, self.get_worker().delete_resource)

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
    
    # ITemplateHelpers
    
    def get_helpers(self):
        return {
            'get_resourcetracker_ogr_wfs': h.get_resourcetracker_ogr_wfs,
            'get_resourcetracker_ogr_wms': h.get_resourcetracker_ogr_wms
        }
    
    def before_show(self, resource_dict):
        """
        see: https://docs.ckan.org/en/2.8/extensions/plugin-interfaces.html#ckan.plugins.interfaces.IResourceController.before_show
        The resource_dict is the dictionary as it would be returned as either a resource_show, a
        package_show or any other api endpoint that would return resource information
        :param resource_dict:
        :return:
        """
        geoserver_url = toolkit.config.get('ckanext.{}.geoserver.url'.format(self.name), 'undefined')
        if geoserver_url.find('undefined') < 0:
            log.debug('''Connected to geoserver, datastore active {1}, resource {2}. '''.format(
                geoserver_url, resource_dict['datastore_active'], resource_dict['id']
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
                            self.set_dict_elements(resource_dict, output_url,
                                                    configuration.workspace_name + ':' + resource_dict['id'],
                                                    configuration.workspace_name + ':' + resource_dict['id'])
                        else:
                            log.debug('''Feature type not found. Do not include in dict.''')
                            self.set_dict_elements(resource_dict, None, None, None)
                    else:
                        log.debug('''Data store not found. Do not include in dict.''')
                        self.set_dict_elements(resource_dict, None, None, None)
                else:
                    log.debug('''Workspace not found. Do not include in dict.''')
                    self.set_dict_elements(resource_dict, None, None, None)
            else:
                log.debug('''Datastore active {0}. Do not include in dict.'''.format(resource_dict['datastore_active']))
                self.set_dict_elements(resource_dict, None, None, None)
        else:
            log.debug(
                '''Not connected to geoserver ({0}). Do not include in dict.'''.format(geoserver_url.find('undefined')))
            self.set_dict_elements(resource_dict, None, None, None)

    def set_dict_elements(self, resource_dict, ows_url, layer_name, feature_type_name):
        resource_dict["ows_url"] = ows_url
        resource_dict["wms_layer_name"] = layer_name
        resource_dict["wfs_featuretype_name"] = feature_type_name