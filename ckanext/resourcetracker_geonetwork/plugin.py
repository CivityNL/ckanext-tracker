import logging
import urlparse

import ckanext.resourcetracker.plugin as resourcetracker

import re
import datetime

import ckan.plugins.toolkit as toolkit
from ckan import model
from ckan.model import Package, GroupExtra
import ckan.plugins as plugins
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from worker.geonetwork import GeoNetworkWorkerWrapper
from worker.geonetwork.rest import GeoNetworkRestApi
from domain import Organization

logging.basicConfig()
log = logging.getLogger(__name__)


class Resourcetracker_GeonetworkPlugin(resourcetracker.ResourcetrackerPlugin):
    plugins.implements(plugins.IConfigurable)

    queue_name = 'geoserver'
    worker = GeoNetworkWorkerWrapper()

    local_cache_active = False
    local_cache_refresh_rate = 300
    local_cache = {}
    local_cache_last_updated = {}

    DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

    REGEX_IDENTIFIER = re.compile('(?<=<dc:identifier>)(.+)(?=<\/dc:identifier>)')
    REGEX_NEXT_RECORD = re.compile('(?<=nextRecord=")([0-9]+)(?=")')

    # IConfigurable
    def configure(self, config):
        super(Resourcetracker_GeonetworkPlugin, self).configure(config)
        self.local_cache_active = toolkit.config.get('ckanext.{}.geonetwork.local_cache_active'.format(self.name), True)

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
        resource_dict["geonetwork_url"] = None
        if resource_dict['datastore_active'] is True:
            try:
                owner_org_id = model.Session.query(Package.owner_org).filter(Package.id == resource_dict['package_id']).one()
                group_extra = model.Session.query(GroupExtra.key, GroupExtra.value).filter(GroupExtra.group_id == owner_org_id).all()
                organization_dict = { 'id': owner_org_id }
                for group_extra in group_extra:
                    organization_dict[group_extra.key] = group_extra.value
                organization = Organization.from_dict(organization_dict)
                if organization.geonetwork_url:
                    log.debug(
                        'Connected to GeoNetwork {0}, datastore active {1}, find {2}. Investigate further.'.format(
                            organization.geonetwork_url, resource_dict['datastore_active'],
                            organization.geonetwork_url.find('undefined')
                        ))
                    if self.local_cache_active is True:
                        self._before_show_using_local_cache(resource_dict, organization)
                    else:
                        self._before_show(resource_dict, organization)
            except:
                log.debug("Could not determine organization for package with id '{id}'"
                          .format(id=resource_dict['package_id']))

    def set_dict_elements(self, resource_dict, geonetwork_url):
        parameters = urlparse.urlparse(geonetwork_url)
        output_url = parameters.scheme + '://' + parameters.hostname
        if parameters.port is not None:
            output_url += ':' + str(parameters.port)
        output_url += parameters.path + '/geonetwork/srv/dut/catalog.search#/metadata/' + resource_dict[
            'id']
        resource_dict["geonetwork_url"] = output_url

    def _before_show(self, resource_dict, organization):
        api = GeoNetworkRestApi(organization)
        record = api.read_record(resource_dict['id'])
        if record is not None:
            set_dict_elements(resource_dict, organization.geonetwork_url)

    def _before_show_using_local_cache(self, resource_dict, organization):
        if self.should_update_local_cache(organization, resource_dict):
            self.update_local_cache(organization)
        if organization.organization_id in self.local_cache and self.local_cache[organization.organization_id] is not None and resource_dict['id'] in self.local_cache[organization.organization_id]:
            set_dict_elements(resource_dict, organization.geonetwork_url)

    def should_update_local_cache(self, organization, resource_dict=None):
        result = False
        if self.local_cache_active is False or not organization.geonetwork_url:
            result = False
        elif organization.organization_id not in self.local_cache_last_updated:
            result = True
        elif self.local_cache_refresh_rate is not None and (datetime.datetime.now() - self.local_cache_last_updated[organization.organization_id]).total_seconds() > self.local_cache_refresh_rate:
            result = True
        elif resource_dict is not None:
            date_string = resource_dict.get('last_modified', None)
            date = None
            if date_string is None:
                date_string = resource_dict.get('created', None)
            if date_string is not None:
                date = datetime.datetime.strptime(date_string, self.DATE_TIME_FORMAT)
            if date is not None and self.local_cache_last_updated[organization.organization_id] < date:
                result = True
        return result

    def update_local_cache(self, organization):
        """
        This method will fetch the names (which are equal to the resource id's) from all the feature_types belonging to
        the workspace and data_store from the configuration and will update the local_cache_last_updated
        @param configuration: Configuration object
        @rtype: None
        """
        result = None
        api = GeoNetworkRestApi(organization)
        result, nextRecord = self.get_records_and_nextrecord(api)
        while nextRecord > 0:
            data, nextRecord = self.get_records_and_nextrecord(api)
            result += data
        self.local_cache[organization.organization_id] = result
        self.local_cache_last_updated[organization.organization_id] = datetime.datetime.now()

    def get_records_url(self, limit=100, offset=1):
        return 'csw?request=GetRecords&service=CSW&version=2.0.2&typeNames=csw%3ARecord&elementsetname=summary&maxRecords={limit}&outputSchema=csw:Record&resultType=results&startPosition={offset}'.\
            format(limit=limit, offset=offset)

    def get_records_and_nextrecord(self, api, offset=1):
        data = None
        records = []
        nextRecord = 0
        try:
            data = api.get('geonetwork/srv/eng', self.get_records_url(offset=offset))
        except:
            log.debug("something went wrong with the GetRecords from {}".format(api.url))
        if data is not None:
            records = REGEX_IDENTIFIER.findall(text)
            nextRecordSearch = REGEX_NEXT_RECORD.search(data)
            nextRecord = int(nextRecordSearch.group(0))
        return records, nextRecord
