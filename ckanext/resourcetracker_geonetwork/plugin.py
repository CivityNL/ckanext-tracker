import logging
import urlparse

import ckanext.resourcetracker.plugin as resourcetracker

import ckan.plugins.toolkit as toolkit
from ckan import model
from ckan.model import Package
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from worker.geonetwork import GeoNetworkWorkerWrapper
from worker.geonetwork.rest import GeoNetworkRestApi
from domain import Organization

logging.basicConfig()
log = logging.getLogger(__name__)


class Resourcetracker_GeonetworkPlugin(resourcetracker.ResourcetrackerPlugin):
    queue_name = 'geoserver'
    worker = GeoNetworkWorkerWrapper()

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')

    def after_create(self, context, resource):
        # Do not put a task on the geonetwork queue in case of a create. This
        # should be handled by geoserver worker. 
        pass

    def after_update(self, context, resource):
        # Do not put a task on the geonetwork queue in case of a update. This
        # should be handled by geoserver worker. 
        pass

    def before_delete(self, context, resource, resources):
        # Do not put a task on the geonetwork queue in case of a delete. This
        # should be handled by geoserver worker. But it doesn't work in case
        # of NGR. 
        pass

    def before_show(self, resource_dict):
        """
        see: https://docs.ckan.org/en/2.8/extensions/plugin-interfaces.html#ckan.plugins.interfaces.IResourceController.before_show
        The resource_dict is the dictionary as it would be returned as either a resource_show, a
        pacakge_show or any other api endpoint that would return resource information
        :param resource_dict:
        :return:
        """
        context = {
            'model': model,
            'ignore_auth': True,
            'defer_commit': True,  # See ckan/ckan#1714
        }
        resource_dict["geonetwork_url"] = None
        if resource_dict['datastore_active'] is True:
            try:
                owner_org_id = model.Session.query(Package.owner_org).filter(Package.id == resource_dict['package_id']).one()
                organization_dict = toolkit.get_action('organization_show')(context, {'id': owner_org_id})
                organization = Organization.from_dict(organization_dict)
                self.set_dict_elements(resource_dict, organization)
            except NoResultFound, exception:
                log.debug("Could not find any organization for package with id '{id}'"
                          .format(id=resource_dict['package_id']))
            except MultipleResultsFound, exception:
                log.debug("Found multiple organizations for package with id '{id}'"
                          .format(id=resource_dict['package_id']))

    def set_dict_elements(self, resource_dict, organization):
        if organization.geonetwork_url:
            log.debug('Connected to GeoNetwork {0}, datastore active {1}, find {2}. Investigate further.'.format(
                organization.geonetwork_url, resource_dict['datastore_active'],
                organization.geonetwork_url.find('undefined')
            ))
            api = GeoNetworkRestApi(organization)
            record = api.read_record(resource_dict['id'])

            if record is not None:
                parameters = urlparse.urlparse(organization.geonetwork_url)
                output_url = parameters.scheme + '://' + parameters.hostname
                if parameters.port is not None:
                    output_url += ':' + str(parameters.port)
                output_url += parameters.path + '/geonetwork/srv/dut/catalog.search#/metadata/' + resource_dict[
                    'id']
                resource_dict["geonetwork_url"] = output_url
            else:
                # log.info('''Record not found. Do not include in dict.''')
                resource_dict["geonetwork_url"] = None
        else:
            # log.info('''Not connected to GeoNetwork. Do not include in dict.''')
            resource_dict["geonetwork_url"] = None