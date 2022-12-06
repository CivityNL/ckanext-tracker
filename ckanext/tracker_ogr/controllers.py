# encoding: utf-8
import logging
import ckan.plugins as p
from ckan import model
from ckanext.tracker_ogr.plugin import OgrTrackerPlugin
from domain import Configuration
import ckanext.tracker.classes.helpers.data as tracker_helpers
from worker.ogr import OgrWorker
import paste.fileapp
from ckan.common import request, response
import ckan.lib.base as base
import ckan.logic as logic
import mimetypes
import os

logging.basicConfig()
log = logging.getLogger(__name__)
abort = base.abort
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
_ = p.toolkit._
g = p.toolkit.g
check_access = p.toolkit.check_access

class ResourceDataController(p.toolkit.BaseController):
    p.implements(p.IConfigurable)
    ogr = OgrTrackerPlugin()

    def ogr_dump(self, resource_id):
        """
        Downloads an OGR exported file of download format specified.
        Spatial filter can apply to get a specified geographical area of the data
        """
        # Check access - resource should belong to public dataset.
        try:
            context = {'model': model, 'user': g.user,
                       'auth_user_obj': g.userobj}
            resource = p.toolkit.get_action('resource_show')(
                context, {'id': resource_id})
        except NotAuthorized:
            abort(403, _('Not authorized to see this page'))
        except NotFound:
            abort(404, _('Resource not found'))


        # Check download_format is supported, otherwise abort. Load formats from ogr-worker
        ogr_worker = OgrWorker()

        file_format = request.GET.get('format', None)
        if file_format:
            file_format = file_format.lower()
        if not file_format:
            abort(404, _('This endpoint requires a format parameter.'))
        if file_format not in ogr_worker.DEFAULT_SUPPORTED_FORMATS:
            abort(404, _('"{}" is not OGR supported. Supported filetypes are: {} ').format(file_format, ", ".join(ogr_worker.DEFAULT_SUPPORTED_FORMATS)))

        query_geometry_shape = request.GET.get('queryGeometry', None)  # Not easy to verify the WKB value validity.
        query_geometry_srid = request.GET.get('srid', None)  # Must correspond a positive integer

        if (query_geometry_shape and not query_geometry_srid) or (not query_geometry_shape and query_geometry_srid):
            abort(404, _('When applying a spatial filter to OGR download, both "query_geometry_shape" and "query_geometry_srid" parameters must be defined with a proper value.'.format(query_geometry_srid)))

        if query_geometry_srid and not query_geometry_srid.isdigit():
            abort(404, _('The geometry srid defined ("{}") is invalid.'.format(query_geometry_srid)))

        # Export OGR file and store temporarily
        worker_name = 'ogr'
        configuration = Configuration.from_dict(tracker_helpers.get_configuration_dict(worker_name))
        # Replace resource metadata 'name' value with original filestore name, to be used for populating the new OGR generated resource.
        file_name = self.get_name_from_url(resource.get('url'))
        ogr_response = ogr_worker.generate_ogr_file(
            configuration=configuration,
            resource_id=resource_id,
            file_format=file_format,
            file_name=file_name,
            query_geometry_shape=query_geometry_shape,
            query_geometry_srid=query_geometry_srid,
            datadictionary=None
            )
        download_format = file_format
        # map .shp extension into .zip extension
        if file_format == 'shp':
            download_format = 'zip'
        # Fulfill request, download OGR file
        if ogr_response.get("success", False):
            filepath = ogr_response.get('path')
            fileapp = paste.fileapp.FileApp(filepath)
            try:
                status, headers, app_iter = request.call_application(fileapp)
            except OSError:
                abort(404, _('Exported OGR file not found.'))
            response.headers.update(dict(headers))
            content_type, content_enc = mimetypes.guess_type("/{}.{}".format(resource_id, download_format))
            if content_type:
                response.headers['Content-Type'] = content_type
            # assign content-disposition to headers to include resource name and proper extension

            response.headers['Content-Disposition'] = 'attachment; filename={resource_name}.{extension}'.format(
                resource_name=file_name,
                extension=download_format)
            response.status = status
            # Delete temporary OGR file
            ogr_worker.delete_ogr_file(filepath)
            return app_iter
        else:
            abort(404, _('OGR file export failed.'))

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
            self.ogr.put_on_a_queue(context, 'resource', self.ogr.get_worker().create_resource, p.toolkit.c.resource, p.toolkit.c.pkg_dict, None, None)
            p.toolkit.redirect_to(
                controller='ckanext.tracker_ogr.controllers:ResourceDataController',
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
    @staticmethod
    def get_name_from_url(url):
        """
        Return name as defined in original URL, removing the original extension
        """
        filename = os.path.basename(url)
        if '.' in filename:
            filename = '.'.join(filename.split('.')[:-1])
        return filename
