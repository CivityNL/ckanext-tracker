import logging

import ckan.plugins as plugins
from ckanext.tracker.classes.base_tracker import BaseTrackerPlugin

logging.basicConfig()
log = logging.getLogger(__name__)

_type = 'package'


class PackageTrackerPlugin(BaseTrackerPlugin):
    """
    This implementation of the BaseTrackerPlugin will tracker all Package related events, which is at this point are the
    "after_create", "after_update", "after_delete" and "after_purge"
    """
    plugins.implements(plugins.IPackageController, inherit=True)

    # IPackageController

    def after_create(self, context, pkg_dict):
        log.info('after_create from {}, action: {}'.format(__name__, 'none'))
        self.put_package_on_a_queue(context, pkg_dict, self.do_create())

    def after_update(self, context, pkg_dict):
        log.info('after_update from {}, action: {}'.format(__name__, 'none'))
        self.put_package_on_a_queue(context, pkg_dict, self.do_update())

    def after_delete(self, context, pkg_dict):
        log.info('after_delete from {}, action: {}'.format(__name__, 'none'))
        self.put_package_on_a_queue(context, pkg_dict, self.do_delete())

    def after_purge(self, context, pkg_dict):
        log.info('after_purge from {}, action: {}'.format(__name__, 'none'))
        self.put_package_on_a_queue(context, pkg_dict, self.do_purge())

    def put_package_on_a_queue(self, context, package, command):
        self.put_on_a_queue(context, _type, package, command)

    # Helpers

    def do_create(self):
        return self.get_worker().create_package

    def do_update(self):
        return self.get_worker().update_package

    def do_delete(self):
        return self.get_worker().delete_package

    def do_purge(self):
        return self.get_worker().purge_package

    def do_upsert(self):
        return self.get_worker().upsert_package

    def get_show_ui(self, context, entity_type, entity_id_or_dict):
        super_result = super(PackageTrackerPlugin, self).get_show_ui(context, entity_type, entity_id_or_dict)
        if super_result is not None:
            return super_result
        return self.add_get_show(context, entity_type, entity_id_or_dict, _type, 'package_show', self.show_ui_for_package_type)

    def get_show_badge(self, context, entity_type, entity_id_or_dict):
        super_result = super(PackageTrackerPlugin, self).get_show_badge(context, entity_type, entity_id_or_dict)
        if super_result is not None:
            return super_result
        return self.add_get_show(context, entity_type, entity_id_or_dict, _type, 'package_show', self.show_badge_for_package_type)

    def show_ui_for_package_type(self, context, package_dict):
        return True

    def show_badge_for_package_type(self, context, package_dict):
        return False

    def get_types(self):
        return super(PackageTrackerPlugin, self).get_types() + [_type]
