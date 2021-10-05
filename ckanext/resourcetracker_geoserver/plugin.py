import datetime
import logging
import threading
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.tracker.classes.resource_tracker import ResourceTrackerPlugin
from domain import Configuration
from helpers import get_resourcetracker_geoserver_wfs, get_resourcetracker_geoserver_wms
from worker.geoserver import GeoServerWorkerWrapper
from worker.geoserver.rest import GeoServerRestApi
from worker.geoserver.rest.model import Workspace, DataStore

logging.basicConfig()
log = logging.getLogger(__name__)


class Resourcetracker_GeoserverPlugin(ResourceTrackerPlugin):
    """No idea what the use is of this Tracker. If you know please add it here"""

    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IConfigurer)

    queue_name = 'geoserver'
    worker = GeoServerWorkerWrapper()
    geoserver_link_field_name = 'geoserver_link_enabled'

    api = None

    local_cache_active = False
    local_cache_refresh_rate = 300
    local_cache = None
    local_cache_last_updated = None
    local_cache_thread_active = None

    DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

    # IConfigurable
    def configure(self, config):
        super(Resourcetracker_GeoserverPlugin, self).configure(config)
        geoserver_url = toolkit.config.get('ckanext.{}.geoserver.url'.format(self.name), None)
        self.local_cache_active = toolkit.config.get('ckanext.{}.geoserver.local_cache_active'.format(self.name), True)
        configuration = self.get_configuration()
        if geoserver_url is not None:
            self.api = GeoServerRestApi(configuration)
            if self.api is not None and self.local_cache_active is True:
                log.debug("starting thread to update local cache")
                self.local_cache_thread_active = True
                threading.Thread(target=self.update_local_cache, args=(configuration, self.api, self.name,)).start()
        else:
            self.local_cache_active = False
            log.debug("No URL for geoserver given. Will ignore all geoserver related checks")

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
        pass

    def after_update(self, context, resource):
        # get package_info to check link
        pkg_dict = toolkit.get_action("package_show")(context,{"id": resource["package_id"]})
        if self.geoserver_link_field_name in pkg_dict and \
                pkg_dict[self.geoserver_link_field_name] == 'True' and \
                resource.get('layer_srid', False):
            log.info('Linking to Geoserver')
            # TODO harmonize before sending to worker
            self.put_resource_on_a_queue(context, resource, self.get_worker().create_datasource)

    def before_show(self, resource_dict):
        """
        see: https://docs.ckan.org/en/2.8/extensions/plugin-interfaces.html#ckan.plugins.interfaces.IResourceController.before_show
        The resource_dict is the dictionary as it would be returned as either a resource_show, a
        pacakge_show or any other api endpoint that would return resource information
        :param resource_dict:
        :return:
        """
        configuration = self.get_configuration()
        # only do something if the resource is datastore_active and we have a geoserver api configured
        if resource_dict['datastore_active'] is True and self.api is not None:
            if self.local_cache_active is True:
                self._before_show_using_local_cache(resource_dict, configuration)
            else:
                self._before_show(resource_dict, configuration)
        else:
            # log.debug('Either Geoserver connection have not been configured or this resource is not datastore_active')
            self.set_dict_elements(resource_dict, None, None)

    def set_dict_elements(self, resource_dict, ows_url, layer_name):
        resource_dict["ows_url"] = ows_url
        resource_dict["ows_layer"] = layer_name
        resource_dict["wms_url"] = get_resourcetracker_geoserver_wms(resource_dict)
        resource_dict["wfs_url"] = get_resourcetracker_geoserver_wfs(resource_dict)

    def _before_show(self, resource_dict, configuration):
        """
        This is a simplified implementation of the original before_show which skips a couple of checks in order to make
        this method run quicker. It will check directly if the feature type exists, regardless if the workspace or data
        store actually exist
        @param resource_dict: dictionary containing the information about the resource
        @param configuration: Configuration object
        """
        workspace = Workspace(name=configuration.workspace_name)
        data_store = DataStore(name=configuration.data_store_name)
        feature_type = self.api.read_feature_type(workspace, data_store, resource_dict['id'])
        if feature_type is not None:
            output_url = toolkit.config.get('ckanext.{}.source_ckan_host'.format(self.name))
            output_url += '/geoserver/{workspace}/ows?'.format(workspace=configuration.workspace_name)
            self.set_dict_elements(resource_dict, output_url, resource_dict['id'])
        else:
            # log.debug('Did not find a corresponding featureType for {id}'.format(id=resource_dict['id']))
            self.set_dict_elements(resource_dict, None, None)

    def _before_show_using_local_cache(self, resource_dict, configuration):
        # type: (dict, Configuration) -> None
        """
        This implementation of the before_show uses a local cache of featureType id's to check if it exists
        @param resource_dict: dictionary containing the information about the resource
        @param configuration: Configuration object
        """
        if self.should_update_local_cache(resource_dict):
            log.debug("starting thread to update local cache")
            self.local_cache_thread_active = True
            threading.Thread(target=self.update_local_cache, args=(configuration, self.api, self.name,)).start()
        if self.local_cache is not None and resource_dict['id'] in self.local_cache:
            output_url = toolkit.config.get('ckanext.{}.source_ckan_host'.format(self.name))
            output_url += '/geoserver/{workspace}/ows?'.format(workspace=configuration.workspace_name)
            self.set_dict_elements(resource_dict, output_url, resource_dict['id'])
        else:
            # log.debug('Did not find a corresponding featureType for {id} in local cache'.format(id=resource_dict['id']))
            self.set_dict_elements(resource_dict, None, None)

    def should_update_local_cache(self, resource_dict=None):
        """
        This method does a couple of checks which might include the resource_dict if given and decides if the
        local_cache should be update, which it returns as a boolean. These checks are
        - if local_cache_active is False or api is None return False
        - if local_cache_last_updated is None (meaning it has never been run before) return True
        - if the time between the last update and now is more the refreshrate (if given) return True
        - if local_cache_last_updated is older then the last_modified or created datetime of the resource_dict (if
            given and a correct date could be extracted) return True
        @rtype: bool
        @param resource_dict: dictionary containing the information about the resource (optional)
        @return: either True or False depending if the local_cache should be updated
        """
        result = False
        if self.local_cache_active is False or self.api is None:
            result = False
        elif self.local_cache_thread_active is True:
            result = False
        elif self.local_cache_last_updated is None:
            result = True
        elif self.local_cache_refresh_rate is not None and (datetime.datetime.now() - self.local_cache_last_updated).total_seconds() > self.local_cache_refresh_rate:
            result = True
        elif resource_dict is not None:
            date_string = resource_dict.get('last_modified', None)
            date = None
            if date_string is None:
                date_string = resource_dict.get('created', None)
            if date_string is not None:
                date = datetime.datetime.strptime(date_string, self.DATE_TIME_FORMAT)
            if date is not None and self.local_cache_last_updated < date:
                result = True
        return result

    @staticmethod
    def update_local_cache(configuration, api, name):
        # type: (Configuration) -> None
        """
        This method will fetch the names (which are equal to the resource id's) from all the feature_types belonging to
        the workspace and data_store from the configuration and will update the local_cache_last_updated
        @param configuration: Configuration object
        @rtype: None
        """
        data = api.get(
            'rest/workspaces/' + configuration.workspace_name + '/datastores/' + configuration.data_store_name,
            'featuretypes')
        result = None
        if data is not None and "featureTypes" in data and "featureType" in data["featureTypes"]:
            result = [feature_type["name"] for feature_type in data["featureTypes"]["featureType"]]
        Resourcetracker_GeoserverPlugin().local_cache = result
        Resourcetracker_GeoserverPlugin().local_cache_last_updated = datetime.datetime.now()
        Resourcetracker_GeoserverPlugin().local_cache_thread_active = False
        log.debug("finished thread to update local cache")
        if Resourcetracker_GeoserverPlugin().local_cache is None:
            geoserver_url = toolkit.config.get('ckanext.{}.geoserver.url'.format(name), None)
            log.debug("Something went wrong fetching the current feature types from geoserver @ {geoserver_url} "
                      "using workspace {workspace} and data_store {data_store}!"
                      .format(geoserver_url=geoserver_url,
                              workspace=configuration.workspace_name,
                              data_store=configuration.data_store_name))
