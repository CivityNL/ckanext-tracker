import logging

import ckan.plugins as plugins
from ckanext.tracker.classes.base_tracker import BaseTrackerPlugin

logging.basicConfig()
log = logging.getLogger(__name__)

_type = 'resource'


class ResourceTrackerPlugin(BaseTrackerPlugin):
    """
    This implementation of the BaseTrackerPlugin will tracker all Resource related events, which is at this point are the
    "after_create", "after_update", and "before_delete"
    """
    plugins.implements(plugins.IResourceController, inherit=True)

    # IResourceController

    def after_create(self, context, resource):
        log.info('after_create from {}, action: {}'.format(__name__, 'none'))
        self.put_resource_on_a_queue(context, resource, self.get_worker().create_resource)

    def after_update(self, context, resource):
        log.info('after_update from {}, action: {}'.format(__name__, 'none'))
        self.put_resource_on_a_queue(context, resource, self.get_worker().update_resource)

    def before_delete(self, context, resource, resources):
        log.info('before_delete from {}, action: {}'.format(__name__, 'none'))
        self.put_resource_on_a_queue(context, resource, self.get_worker().delete_resource)

    def put_resource_on_a_queue(self, context, resource, command):
        self.put_on_a_queue(context, _type, resource, command)

    def get_show_ui(self, context, entity_type, entity_id_or_dict):
        super_result = super(ResourceTrackerPlugin, self).get_show_ui(context, entity_type, entity_id_or_dict)
        if super_result is not None:
            return super_result
        return self.add_get_show(context, entity_type, entity_id_or_dict, _type, 'resource_show', self.show_ui_for_resource_type)

    def get_show_badge(self, context, entity_type, entity_id_or_dict):
        super_result = super(ResourceTrackerPlugin, self).get_show_badge(context, entity_type, entity_id_or_dict)
        if super_result is not None:
            return super_result
        return self.add_get_show(context, entity_type, entity_id_or_dict, _type, 'resource_show', self.show_badge_for_resource_type)

    def show_ui_for_resource_type(self, context, resource_dict):
        return True

    def show_badge_for_resource_type(self, context, resource_dict):
        return False

    def get_types(self):
        return super(ResourceTrackerPlugin, self).get_types() + [_type]
