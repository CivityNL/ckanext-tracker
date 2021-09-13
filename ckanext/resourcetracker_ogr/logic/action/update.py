
import logging

import ckan.logic as logic
import ckan.plugins as plugins
import ckanext.datapusher.interfaces as datapusher_interfaces
import ckanext.resourcetracker_ogr.interface as resourcetracker_ogr_interfaces
import ckanext.xloader.interfaces as xloader_interfaces

logging.basicConfig()
log = logging.getLogger(__name__)

_get_or_bust = logic.get_or_bust


def ogr_can_upload_hook(context, data_dict):
    """
    This action will call all `can_upload` methods implemented either in the IDataPusher, IXloader or IOgr
    interfaces
    @param context:
    @param resource_dict:
    """
    log.info("[ogr_can_upload_hook] {}".format(data_dict))

    resource_id = _get_or_bust(data_dict, 'id')

    for plugin in plugins.PluginImplementations(datapusher_interfaces.IDataPusher):
        log.info('running IDataPusher implementation of can_upload for {}'.format(plugin))
        plugin.can_upload(resource_id)

    for plugin in plugins.PluginImplementations(xloader_interfaces.IXloader):
        log.info('running IXloader implementation of can_upload for {}'.format(plugin))
        plugin.can_upload(resource_id)

    for plugin in plugins.PluginImplementations(resourcetracker_ogr_interfaces.IOgr):
        log.info('running IOgr implementation of can_upload for {}'.format(plugin))
        plugin.can_upload(resource_id)


def ogr_after_upload_hook(context, data_dict):
    """
    This action will call all `after_upload` methods implemented either in the IDataPusher, IXloader or IOgr
    interfaces
    @param context:
    @param resource_dict:
    """
    log.info("[ogr_before_upload_hook] {}".format(data_dict))

    resource_id = _get_or_bust(data_dict, 'id')

    res_dict = plugins.toolkit.get_action('resource_show')(
        context, {'id': resource_id})

    pkg_dict = plugins.toolkit.get_action('package_show')(
        context, {'id': res_dict['package_id']})

    for plugin in plugins.PluginImplementations(datapusher_interfaces.IDataPusher):
        log.info('running IDataPusher implementation of after_upload for {}'.format(plugin))
        plugin.after_upload(context, res_dict, pkg_dict)

    for plugin in plugins.PluginImplementations(xloader_interfaces.IXloader):
        log.info('running IXloader implementation of after_upload for {}'.format(plugin))
        plugin.after_upload(context, res_dict, pkg_dict)

    for plugin in plugins.PluginImplementations(resourcetracker_ogr_interfaces.IOgr):
        log.info('running IOgr implementation of after_upload for {}'.format(plugin))
        plugin.after_upload(context, res_dict, pkg_dict)
