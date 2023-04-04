from ckanext.tracker_base.auth import _callback_hook as auth_callback_hook


def geoserver_callback_hook(context, data_dict):
    return auth_callback_hook(context, data_dict)
