import logging
from flask import Blueprint
from flask.views import MethodView
import ckan.plugins.toolkit as toolkit


logging.basicConfig()
log = logging.getLogger(__name__)

tracker = Blueprint('tracker', __name__)


class ResourceTrackerView(MethodView):

    def get(self, id, resource_id):
        try:
            pkg_dict = toolkit.get_action('package_show')(
                None, {'id': id}
            )
            resource = toolkit.get_action('resource_show')(
                None, {'id': resource_id}
            )
        except (toolkit.ObjectNotFound, toolkit.NotAuthorized):
            toolkit.abort(404, toolkit._('Resource not found'))

        return toolkit.render('tracker/resource_data.html', extra_vars={
            'pkg_dict': pkg_dict,
            'resource': resource,
            'dataset_type': pkg_dict.get("type", "dataset")
        })


class PackageTrackerView(MethodView):

    def get(self, id):
        try:
            pkg_dict = toolkit.get_action('package_show')(
                None, {'id': id}
            )
        except (toolkit.ObjectNotFound, toolkit.NotAuthorized):
            toolkit.abort(404, toolkit._('Package not found'))

        return toolkit.render('tracker/package_data.html', extra_vars={
            'pkg_dict': pkg_dict,
            'dataset_type': pkg_dict.get("type", "dataset")
        })


class AdminTrackerView(MethodView):
    def get(self):
        return toolkit.render('admin/trackers.html')


tracker.add_url_rule(u'/dataset/<id>/resource/<resource_id>/trackers', view_func=ResourceTrackerView.as_view(str(u'resource')))
tracker.add_url_rule(u'/dataset/<id>/trackers', view_func=PackageTrackerView.as_view(str(u'package')))
tracker.add_url_rule(u'/ckan-admin/trackers', view_func=AdminTrackerView.as_view(str(u'admin')))
