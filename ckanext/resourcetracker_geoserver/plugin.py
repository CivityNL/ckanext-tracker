import ckan.plugins.toolkit as toolkit
from ckanext.tracker.classes.resource_tracker import ResourceTrackerPlugin
import helpers as h
import ckanext.tracker.classes.helpers as tracker_helpers
from worker.geoserver import GeoServerWorkerWrapper
from worker.geoserver.rest import GeoServerRestApi
from worker.geoserver.rest.model import Workspace, DataStore, FeatureType
import ckan.plugins as plugins
import json
import logging
logging.basicConfig()
log = logging.getLogger(__name__)


class Resourcetracker_GeoserverPlugin(ResourceTrackerPlugin):
    """
    - Handles resource triggers when GeoServer link is enabled.
    - Triggers Geoserver-Worker when conditions are met.
    """
    plugins.implements(plugins.IConfigurer)
    queue_name = 'geoserver'
    worker = GeoServerWorkerWrapper()
    geoserver_link_field_name = 'geoserver_link_enabled'
    api = None
    workspace = None
    data_store = None
    GEOSERVER_METADATA_LIST = ['name', 'description', 'layer_extent', 'layer_srid']


    # IConfigurable
    def configure(self, config):
        super(Resourcetracker_GeoserverPlugin, self).configure(config)
        geoserver_url = toolkit.config.get('ckanext.{}.geoserver.url'.format(self.name), None)
        configuration = self.get_configuration()
        if geoserver_url is not None:
            self.api = GeoServerRestApi(configuration)
            self.workspace = Workspace(name=configuration.workspace_name)
            self.data_store = DataStore(name=configuration.data_store_name)

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')

    # IResourceController
    def after_create(self, context, resource):
        pass

    def after_update(self, context, resource):
        # get package_info to check link
        configuration = self.get_configuration()
        package = toolkit.get_action("package_show")(context, {"id": resource["package_id"]})
        if self.should_publish_to_geoserver(configuration, package, resource):
            self.put_resource_on_a_queue(context, resource, self.get_worker().create_datasource)

    def should_publish_to_geoserver(self, configuration, package, resource):
        '''
        multiple criteria to be met in order to publish to geoserver:
            1. geoserver_link enabled in package metadata
            2. layer_srid populated in resource metadata
            3. GeoServer FeatureType to not exist
            or FeatureType to exist and geoserver-related metadata to be changed
        '''
        if not tracker_helpers.geoserver_link_is_enabled(package):
            return False
        if not ('layer_srid' in resource and resource.get('layer_srid')):
            return False
        if not ('layer_extent' in resource and resource.get('layer_extent')):
            return False
        if resource.get('format').lower in ['wms', 'wfs']:
            return False
        geoserver_feature_type = self.get_geoserver_feature_type(configuration, resource)
        if not geoserver_feature_type:
            # Case layer does not exist(first iteration) -> create geoserver feature_type
            return True
        else:
            if not self.metadata_equals(key_list=self.GEOSERVER_METADATA_LIST,
                                        metadata_origin=resource,
                                        metadata_remote=geoserver_feature_type):
                # Case layer exists but 'GEOSERVER_METADATA_LIST' metadata changed -> update geoserver feature_type
                return True
            return False

    def get_geoserver_feature_type(self, configuration, resource_dict):
        '''
        Geoserver RestAPI call to check if feature exists in Geoserver environment
        '''
        feature_type_name = h.get_geoserver_feature_type_name(configuration, resource_dict)
        feature_type = self.api.read_feature_type(self.workspace, self.data_store, feature_type_name)
        if feature_type:
            return FeatureType.to_dict(feature_type)

    def metadata_equals(self, key_list, metadata_origin, metadata_remote):
        '''
        Customized for Geoserver metadata comparison
        '''
        for key in key_list:
            if key == 'layer_extent':
                origin_layer_extent_dict = json.loads(metadata_origin.get(key))
                remote_layer_extent_dict = json.loads(metadata_remote.get(key))
                if not self.layer_extend_is_equal(origin_layer_extent_dict, remote_layer_extent_dict):
                    return False
            else:
                if metadata_origin.get(key, None) != metadata_remote.get(key, None):
                    return False
        return True

    @staticmethod
    def layer_extend_is_equal(origin_layer_extent_dict, remote_layer_extent_dict):
        '''
        Function to compare layer extend while overriding the
        decimal precision difference between ogr-side and geoserver-side coordinates.
        '''
        if len(origin_layer_extent_dict) == len(remote_layer_extent_dict) == 4:
            for index, coord in enumerate(origin_layer_extent_dict):
                origin_rounded_coord = '{:.10f}'.format(origin_layer_extent_dict[index])
                remote_rounded_coord = '{:.10f}'.format(remote_layer_extent_dict[index])
                if origin_rounded_coord != remote_rounded_coord:
                    return False
            return True

