import urllib
import logging
log = logging.getLogger(__name__)

def get_resourcetracker_geoserver_wfs(res):
    result = ''
    url = res.get("ows_url")
    params_dict = {
        'service': 'WFS',
        'version': '2.0.0',
        'request': 'GetFeature',
        'typeName': res.get("ows_layer"),
        'maxFeatures': 50,
        'outputFormat': 'application/json'
    }
    params = urllib.urlencode(params_dict)
    if url is not None:
        result = url + params
    return result


def get_resourcetracker_geoserver_wms(res):
    result = ''
    url = res.get("ows_url")
    params_dict = {
        'service': 'WMS',
        'version': '1.1.0',
        'request': 'GetMap',
        'layers': res.get("ows_layer"),
        'bbox': get_bbox(res),
        'width': 768,
        'height': 384,
        'srs': 'EPSG:4326',
        'format': 'image/png'
    }
    params = urllib.urlencode(params_dict)
    if url is not None:
        result = url + params
    return result


def get_bbox(res):
    # default_bbox = '5,45,15,60'
    bbox_raw = res.get('layer_extent')
    if (isinstance(bbox_raw, list)):
        bbox = ', '.join(str(e) for e in bbox_raw)
    elif (isinstance(bbox_raw, unicode)) or (isinstance(bbox_raw, str)):
        bbox = bbox_raw.strip('[]')
    else:
        bbox = None
    return bbox


def get_feature_type_name(configuration, resource_dict):
    """
    In default settings, layer name should equal to resource_id.
    Due to XML errors in Geoserver side when layer name (resource_id string) starts with a number,
    a prefix string should be applied on the layer name. https://civity.atlassian.net/browse/DEV-3915.
    """

    geoserver_layer_prefix = configuration.geoserver_layer_prefix
    feature_type_name = '{prefix}{resource_id}'.format(prefix=geoserver_layer_prefix, resource_id=resource_dict['id'])
    log.debug('[helpers] get_feature_type_name: {name}'.format(name=feature_type_name))
    return feature_type_name


def get_resource_id_from_feature_type_name(configuration, feature_type_name):
    """
    In default settings, this returns the exact same value of variable 'feature_type_name'.
    If a geoserver_layer_prefix is defined, it will strip of the prefix string.
    """
    geoserver_layer_prefix = configuration.geoserver_layer_prefix
    resource_id = feature_type_name.lstrip(geoserver_layer_prefix)
    return resource_id

