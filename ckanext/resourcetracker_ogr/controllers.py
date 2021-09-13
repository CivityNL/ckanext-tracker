import logging

import ckan.plugins as p
import ckan.plugins as plugins
from ckan import model
from ckanext.resourcetracker_ogr.plugin import Resourcetracker_OgrPlugin

logging.basicConfig()
log = logging.getLogger(__name__)

_ = p.toolkit._


class ResourceDataController(p.toolkit.BaseController):
    plugins.implements(plugins.IConfigurable)
    ogr = Resourcetracker_OgrPlugin()

    def resource_data(self, id, resource_id):
        try:
            p.toolkit.c.pkg_dict = p.toolkit.get_action('package_show')(
                None, {'id': id}
            )
            p.toolkit.c.resource = p.toolkit.get_action('resource_show')(
                None, {'id': resource_id}
            )
        except (p.toolkit.ObjectNotFound, p.toolkit.NotAuthorized):
            p.toolkit.abort(404, _('Resource not found'))

        if p.toolkit.request.method == 'POST':
            context = {'model': model, 'ignore_auth': True, 'defer_commit': True, 'user': 'automation'}
            self.ogr.put_resource_on_a_queue(context, p.toolkit.c.resource, self.ogr.get_worker().create_resource)
            p.toolkit.redirect_to(
                controller='ckanext.resourcetracker_ogr.controllers:ResourceDataController',
                action='resource_data',
                id=id,
                resource_id=resource_id
            )
        #TODO build a status call to get the datastore call progress (as built for xloader)
        return p.toolkit.render('ogr/resource_data.html',
                            extra_vars={
                                'status': {},
                                'resource': p.toolkit.c.resource,
                                'pkg_dict': p.toolkit.c.pkg_dict
                            })