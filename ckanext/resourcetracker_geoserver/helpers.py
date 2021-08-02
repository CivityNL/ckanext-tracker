import urllib


def get_resourcetracker_geoserver_wfs(res):
    result = ''
    url = res.get("ows_url")
    params_dict = {
        'service': 'WFS',
        'version': '1.0.0',
        'request': 'GetFeature',
        'typeName': res.get("wms_layer_name"),
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
        'layers': res.get("wms_layer_name"),
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
    bbox_raw = res.get('layer_extent', '-180.0,-90.0,180.0,90.0') # default value globe
    bbox = bbox_raw.strip('[]')
    return bbox