import logging

import ckan.plugins as plugins
from ckan.plugins.toolkit import _, c, get_action, ObjectNotFound, NotAuthorized, abort, request, render, h
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

        if request.method == 'POST':
            data = dict_fns.unflatten(tuplize_dict(parse_params(
                request.params)))
            self.upsert_data(data.get("name"), data.get("type"), c.resource, 'resource_data', id, resource_id)

        return render('tracker/resource_data.html')

    def package_data(self, id):
        try:
            c.pkg_dict = get_action('package_show')(
                None, {'id': id}
            )
        except (ObjectNotFound, NotAuthorized):
            abort(404, _('Package not found'))

        if request.method == 'POST':
            data = dict_fns.unflatten(tuplize_dict(parse_params(
                request.params)))
            self.upsert_data(data.get("name"), data.get("type"), c.pkg_dict, 'package_data', id)

        return render('tracker/package_data.html')

    def upsert_data(self, name, entity_type, entity, action, id, resource_id=None):
        log.info("upsert_data(name = '{}', entity_type = '{}', entity = '{}')".format(name, entity_type, entity))
        tracker = TrackerBackend.get_tracker(entity_type, name)
        log.info(tracker)
        if tracker is not None:
            context = {'model': model, 'session': model.Session,
                       'user': c.user}
            log.info("put on a queue")
            tracker.enqueue_method(context, entity_type, entity, tracker.upsert_method)
        h.redirect_to(
            controller='ckanext.tracker.controllers:TrackerController',
            action=action,
            id=id,
            resource_id=resource_id
        )
