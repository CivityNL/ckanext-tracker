import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.tracker.classes.base_tracker import BaseTrackerPlugin

logging.basicConfig()
log = logging.getLogger(__name__)

_type = 'datastore'

class DataStoreTrackerPlugin(BaseTrackerPlugin):
    """
    This implementation of the BaseTrackerPlugin will tracker all DataStore related events, which is at this point the
    "after_upload"
    """

    if plugins.plugin_loaded('datapusher'):
        import ckanext.datapusher.plugin as datapusher
        plugins.implements(datapusher.IDataPusher, inherit=True)
    elif plugins.plugin_loaded('xloader'):
        import ckanext.xloader.interfaces as xloader_interfaces
        plugins.implements(xloader_interfaces.IXloader, inherit=True)
    elif plugins.plugin_loaded('resourcetracker_ogr'):
        import ckanext.resourcetracker_ogr.interface as resourcetracker_ogr_interfaces
        plugins.implements(resourcetracker_ogr_interfaces.IOgr, inherit=True)
    else:
        raise toolkit.ValidationError(
            {'Plugin': ['DataPusher or Xloader or Resourcetracker_ogr Extension must be enabled']})

    # IXloader/IDataPusher
    # Both Extensions have the same Interface hook points, check docs:
    # https://github.com/ckan/ckan/blob/master/ckanext/datapusher/interfaces.py
    # https://github.com/ckan/ckanext-xloader/blob/master/ckanext/xloader/interfaces.py

    def after_upload(self, context, resource_dict, dataset_dict):
        log.info('after_upload from {}, action: {}'.format(__name__, 'none'))
        self.put_datastore_on_a_queue(context, resource_dict, self.get_worker().create_datasource)

    def put_datastore_on_a_queue(self, context, resource, command):
        self.put_on_a_queue(context, _type, resource, command)

    def get_show_ui(self, context, entity_type, entity_id_or_dict):
        super_result = super(DataStoreTrackerPlugin, self).get_show_ui(context, entity_type, entity_id_or_dict)
        if super_result is not None:
            return super_result
        return self.add_get_show(context, entity_type, entity_id_or_dict, _type, 'resource_show', self.show_ui_for_datastore_type)

    def get_show_badge(self, context, entity_type, entity_id_or_dict):
        super_result = super(DataStoreTrackerPlugin, self).get_show_badge(context, entity_type, entity_id_or_dict)
        if super_result is not None:
            return super_result
        return self.add_get_show(context, entity_type, entity_id_or_dict, _type, 'resource_show', self.show_badge_for_datastore_type)

    def show_ui_for_datastore_type(self, context, resource_dict):
        return True

    def show_badge_for_datastore_type(self, context, resource_dict):
        return False

    def get_types(self):
        return super(DataStoreTrackerPlugin, self).get_types() + [_type]
