import urllib


def get_resourcetracker_geoserver_wfs(res):
    result = ''
    url = res.get("ows_url")
    params_dict = {
        'service': 'WFS',
        'version': '1.0.0',
        'request': 'GetFeature',
        'typeName': res.get("wfs_featuretype_name"),
        'maxFeatures': 50
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
        'bbox': '-180.0,-90.0,180.0,90.0',
        'width': 768,
        'height': 384,
        'srs': 'EPSG:4326',
        'format': 'image/png'
    }
    params = urllib.urlencode(params_dict)
    if url is not None:
        result = url + params
    return result
