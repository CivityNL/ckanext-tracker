from ckanext.tracker_geoserver.interface import ITrackerGeoserver
from ckanext.tracker.classes import action_callback_hook


def geoserver_callback_hook(context, data_dict):
    """
    This action will call all `after_upload` methods implemented either in the IDataPusher, IXloader or IOgr
    interfaces
    @param context:
    @param resource_dict:
    """
    action_callback_hook(context, data_dict, ITrackerGeoserver)
