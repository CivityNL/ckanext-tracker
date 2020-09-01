import logging
import json
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.tracker.plugin as tracker

logging.basicConfig()
log = logging.getLogger(__name__)


class PackagetrackerPlugin(tracker.TrackerPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IPackageController, inherit=True)

    mapper = None

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'packagetracker')

    # IPackageController

    def after_create(self, context, pkg_dict):
        log.info('after_create from {}, action: {}'.format(__name__, 'none'))
        self.put_on_a_queue(context, pkg_dict, self.do_create())

    def after_update(self, context, pkg_dict):
        log.info('after_update from {}, action: {}'.format(__name__, 'none'))
        self.put_on_a_queue(context, pkg_dict, self.do_update())

    def after_delete(self, context, pkg_dict):
        log.info('after_delete from {}, action: {}'.format(__name__, 'none'))
        self.put_on_a_queue(context, pkg_dict, self.do_delete())

    def after_purge(self, context, pkg_dict):
        log.info('after_purge from {}, action: {}'.format(__name__, 'none'))
        self.put_on_a_queue(context, pkg_dict, self.do_purge())

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

    def get_data(self, context, data):
        pkg_dict = toolkit.get_action('package_show')(context, {'id': data['id']})
        if self.mapper is not None:
            package_data = self.mapper.map_package_to_harmonized(self.get_configuration(), pkg_dict)
        else:
            package_data = json.dumps(pkg_dict)
        return package_data