import urllib
import logging
import json

from ckanext.tracker.classes.helpers import link_is_enabled
from worker.geoserver.rest.model import FeatureType

log = logging.getLogger(__name__)

DEFAULT_WMS_VERSION = '1.3.0'
DEFAULT_WFS_VERSION = '2.0.0'
DEFAULT_WMS_GETMAP_WIDTH = 768
DEFAULT_WMS_GETMAP_HEIGHT = 384
DEFAULT_WMS_SRS = 'EPSG:4326'

GEOSERVER_METADATA_LIST = ['name', 'description', 'layer_extent', 'layer_srid']


def geoserver_link_is_enabled(package):
    return link_is_enabled(package, 'geoserver_link_enabled')


def get_geoserver_feature_type_name(configuration, resource_dict):
    """
    In default settings, layer name should equal to resource_id.
    Due to XML errors in Geoserver side when layer name (resource_id string) starts with a number,
    a prefix string should be applied on the layer name. https://civity.atlassian.net/browse/DEV-3915.
    """
    geoserver_layer_prefix = configuration.geoserver_layer_prefix
    feature_type_name = '{prefix}{resource_id}'.format(prefix=geoserver_layer_prefix, resource_id=resource_dict['id'])

    return feature_type_name


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


def metadata_equals(key_list, metadata_origin, metadata_remote):
    '''
    Customized for Geoserver metadata comparison
    '''
    for key in key_list:
        if key == 'layer_extent':
            origin_layer_extent_dict = json.loads(metadata_origin.get(key))
            remote_layer_extent_dict = json.loads(metadata_remote.get(key))
            if not layer_extend_is_equal(origin_layer_extent_dict, remote_layer_extent_dict):
                return False
        else:
            if metadata_origin.get(key, None) != metadata_remote.get(key, None):
                return False
    return True


def get_geoserver_feature_type(configuration, api, workspace, data_store, resource_dict):
    '''
    Geoserver RestAPI call to check if feature exists in Geoserver environment
    '''
    log.debug('Geoserver RestAPI call to check if feature exists in Geoserver environment')
    feature_type_name = get_geoserver_feature_type_name(configuration, resource_dict)
    feature_type = api.read_feature_type(workspace, data_store, feature_type_name)
    if feature_type:
        return FeatureType.to_dict(feature_type)


def should_publish_to_geoserver(configuration, api, workspace, data_store, package, resource):
    # todo accept resource_changes as a parameter (and take into account they don't come from the create)
    '''
    multiple criteria to be met in order to publish to geoserver:
        1. geoserver_link enabled in package metadata
        2. layer_srid populated in resource metadata
        3. GeoServer FeatureType does not exist
        or FeatureType exists and geoserver-related metadata changed
    '''
    if not geoserver_link_is_enabled(package):
        log.debug('geoserver_link_is_enabled is NOT enabled')
        return False
    if not ('layer_srid' in resource and resource.get('layer_srid')):
        log.debug('layer_srid is NOT present')
        return False
    if not ('layer_extent' in resource and resource.get('layer_extent')):
        log.debug('layer_extent is NOT present')
        return False
    if not ('datastore_active' in resource and resource.get('datastore_active')):
        log.debug('datastore_active is NOT present or is False')
        return False
    if resource.get('format').lower in ['wms', 'wfs']:
        log.debug('format({}) is NOT in [wms, wfs]'.format(resource.get('format').lower))
        return False
    # todo potentially remove this to the worker side
    geoserver_feature_type = get_geoserver_feature_type(configuration, api, workspace, data_store, resource)
    if not geoserver_feature_type:
        log.debug('geoserver_feature_type is NOT present so it SHOULD CREATE IT')
        # Case layer does not exist(first iteration) -> create geoserver feature_type
        return True
    else:
        log.debug('geoserver_feature_type is present. comparing it to the metadata')
        if not metadata_equals(key_list=GEOSERVER_METADATA_LIST,
                               metadata_origin=resource,
                               metadata_remote=geoserver_feature_type):
            # Case layer exists but 'GEOSERVER_METADATA_LIST' metadata changed -> update geoserver feature_type
            log.debug('metadata needs to be updated')
            return True
        log.debug('metadata is the same do not update')
        return False


def should_unpublish_to_geoserver(configuration, api, workspace, data_store, package, resource):
    '''
    multiple criteria to be met in order to unpublish from geoserver:
        1. geoserver_link enabled in package metadata
    '''
    log.debug('should_unpublish_to_geoserver ALWAYS returns True')
    return True
