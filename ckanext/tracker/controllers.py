import logging

import ckan.plugins as plugins
from ckan.plugins.toolkit import _, c, get_action, ObjectNotFound, NotAuthorized, abort, request, render, h, redirect_to
from ckan.logic import tuplize_dict, parse_params
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.model as model

from ckanext.tracker.backend import TrackerBackend

logging.basicConfig()
log = logging.getLogger(__name__)


class TrackerController(plugins.toolkit.BaseController):
    """
    This Controller manages the showing of tragger information related to this resource
    see also:
    - tracker.plugin.py#35
    """
    plugins.implements(plugins.IConfigurable)

    def resource_data(self, id, resource_id):
        try:
            c.pkg_dict = get_action('package_show')(
                None, {'id': id}
            )
            c.resource = get_action('resource_show')(
                None, {'id': resource_id}
            )
        except (ObjectNotFound, NotAuthorized):
            abort(404, _('Resource not found'))

        return render('tracker/resource_data.html')

    def package_data(self, id):
        try:
            c.pkg_dict = get_action('package_show')(
                None, {'id': id}
            )
        except (ObjectNotFound, NotAuthorized):
            abort(404, _('Package not found'))

        return render('tracker/package_data.html')

    def queues(self):
        return render('admin/trackers.html')
