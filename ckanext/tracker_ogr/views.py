import logging

import flask
from flask import Blueprint
from flask.views import MethodView
from ckan import model
import os
from ckan.plugins import toolkit
import mimetypes

logging.basicConfig()
log = logging.getLogger(__name__)


def _get_context():
    return {
        u'model': model,
        u'session': model.Session,
        u'user': toolkit.g.user,
        u'auth_user_obj': toolkit.g.userobj,
        u'for_view': True
    }


def _get_name_from_url(url):
    """
    Return name as defined in original URL, removing the original extension
    """
    filename = os.path.basename(url)
    if '.' in filename:
        filename = '.'.join(filename.split('.')[:-1])
    return filename


def _get_pkg_dict(id):
    pkg_dict = None
    try:
        pkg_dict = toolkit.get_action('package_show')(_get_context(), {'id': id})
    except (toolkit.ObjectNotFound, toolkit.NotAuthorized):
        toolkit.abort(404, toolkit._('Package not found'))
    return pkg_dict


def _get_res_dict(id):
    res_dict = None
    try:
        res_dict = toolkit.get_action('resource_show')(_get_context(), {'id': id})
    except (toolkit.ObjectNotFound, toolkit.NotAuthorized):
        toolkit.abort(404, toolkit._('Resource not found'))
    return res_dict


def resource_tracker_ogr_view(ogr_tracker_plugin):
    class ResourceTrackerOgrView(MethodView):

        ogr = ogr_tracker_plugin

        def get(self, id, resource_id):
            pkg_dict = _get_pkg_dict(id)
            extra_vars = {
                'status': {},
                'resource': _get_res_dict(resource_id),
                'pkg_dict': pkg_dict,
                'dataset_type': pkg_dict.get("type", "dataset")
            }
            log.info("ResourceTrackerOgrView::extra_vars = {}".format(extra_vars))
            return toolkit.render('ogr/resource_data.html', extra_vars=extra_vars)

        def post(self, id, resource_id):
            context = {'model': model, 'ignore_auth': True, 'defer_commit': True, 'user': 'automation'}
            self.ogr.put_on_a_queue(context, 'resource', self.ogr.get_worker().create_resource,
                                    _get_res_dict(resource_id), _get_pkg_dict(id), None, None)
            return toolkit.redirect_to(u'tracker_ogr.resource', id=id, resource_id=resource_id)

    return ResourceTrackerOgrView


def dump_tracker_ogr_view(ogr_tracker_plugin):

    class DumpTrackerOgrView(MethodView):

        ogr = ogr_tracker_plugin

        def get(self, resource_id):
            res_dict = _get_res_dict(resource_id)
            ogr_worker = self.ogr.get_worker().create_worker()

            file_format = toolkit.request.args.get('format', None)
            query_geometry_shape = toolkit.request.args.get('queryGeometry', None)  # Not easy to verify the WKB value validity.
            query_geometry_srid = toolkit.request.args.get('srid', None)  # Must correspond a positive integer
            if not file_format:
                toolkit.abort(404, toolkit._('This endpoint requires a format parameter.'))
            file_format = file_format.lower()
            if file_format not in ogr_worker.DEFAULT_SUPPORTED_FORMATS:
                toolkit.abort(404, toolkit._('"{}" is not OGR supported. Supported filetypes are: {} ').format(file_format, ", ".join(ogr_worker.DEFAULT_SUPPORTED_FORMATS)))
            if (query_geometry_shape and not query_geometry_srid) or (not query_geometry_shape and query_geometry_srid):
                toolkit.abort(404, toolkit._('When applying a spatial filter to OGR download, both "query_geometry_shape" and "query_geometry_srid" parameters must be defined with a proper value.'))
            if query_geometry_srid and not query_geometry_srid.isdigit():
                toolkit.abort(404, toolkit._('The geometry srid defined ("{}") is invalid.'.format(query_geometry_srid)))

            # Export OGR file and store temporarily
            worker_name = 'ogr'
            self.ogr.get_configuration()
            # Replace resource metadata 'name' value with original filestore name, to be used for populating the new OGR generated resource.
            file_name = _get_name_from_url(res_dict.get('url'))
            ogr_response = ogr_worker.generate_ogr_file(
                configuration=self.ogr.get_configuration(),
                resource_id=resource_id,
                file_format=file_format,
                file_name=file_name,
                query_geometry_shape=query_geometry_shape,
                query_geometry_srid=query_geometry_srid,
                datadictionary=None
            )
            # map .shp extension into .zip extension
            if file_format == 'shp':
                download_format = 'zip'
            else:
                download_format = file_format
            # Fulfill request, download OGR file
            if ogr_response.get("success", False):
                filepath = ogr_response.get('path')
                response = flask.send_file(filepath)
                content_type, content_enc = mimetypes.guess_type("/{}.{}".format(resource_id, download_format))
                if content_type:
                    response.headers['Content-Type'] = content_type
                # assign content-disposition to headers to include resource name and proper extension

                response.headers['Content-Disposition'] = 'attachment; filename={resource_name}.{extension}'.format(
                    resource_name=file_name,
                    extension=download_format)
                # Delete temporary OGR file
                ogr_worker.delete_ogr_file(filepath)
                return response
            else:
                toolkit.abort(404, toolkit._('OGR file export failed.'))

    return DumpTrackerOgrView


def create_blueprint(ogr_tracker_plugin):
    blueprint = Blueprint('tracker_ogr', __name__)
    blueprint.add_url_rule(u'/dataset/<id>/resource_data/<resource_id>', view_func=resource_tracker_ogr_view(ogr_tracker_plugin).as_view(str(u'resource')))
    blueprint.add_url_rule(u'/ogr/dump/<resource_id>', view_func=dump_tracker_ogr_view(ogr_tracker_plugin).as_view(str(u'dump')))
    return blueprint
