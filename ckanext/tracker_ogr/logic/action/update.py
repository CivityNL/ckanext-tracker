from ckanext.tracker_ogr.interface import ITrackerOgr
from ckanext.tracker_base import action_callback_hook


def ogr_callback_hook(context, data_dict):
    """
    This action will call all `after_upload` methods implemented either in the IDataPusher, IXloader or IOgr
    interfaces
    @param context:
    @param resource_dict:
    """
    action_callback_hook(context, data_dict, ITrackerOgr)
