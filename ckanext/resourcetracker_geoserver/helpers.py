import urllib
import logging
log = logging.getLogger(__name__)

DEFAULT_WMS_VERSION = '1.3.0'
DEFAULT_WFS_VERSION = '2.0.0'
DEFAULT_WMS_GETMAP_WIDTH = 768
DEFAULT_WMS_GETMAP_HEIGHT = 384
DEFAULT_WMS_SRS = 'EPSG:4326'

def get_geoserver_feature_type_name(configuration, resource_dict):
    """
    In default settings, layer name should equal to resource_id.
    Due to XML errors in Geoserver side when layer name (resource_id string) starts with a number,
    a prefix string should be applied on the layer name. https://civity.atlassian.net/browse/DEV-3915.
    """
    geoserver_layer_prefix = configuration.geoserver_layer_prefix
    feature_type_name = '{prefix}{resource_id}'.format(prefix=geoserver_layer_prefix, resource_id=resource_dict['id'])

    return feature_type_name


