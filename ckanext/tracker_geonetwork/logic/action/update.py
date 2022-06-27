from ckanext.tracker_geonetwork.interface import ITrackerGeonetwork
from ckanext.tracker.classes import action_callback_hook


def geonetwork_callback_hook(context, data_dict):
    """
    This action will call all `after_upload` methods implemented either in the IDataPusher, IXloader or IOgr
    interfaces
    @param context:
    @param resource_dict:
    """
    action_callback_hook(context, data_dict, ITrackerGeonetwork)
