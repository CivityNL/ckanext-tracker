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



