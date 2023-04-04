from ckanext.tracker_base import auth_callback_hook


def geoserver_callback_hook(context, data_dict):
    return auth_callback_hook(context, data_dict)
