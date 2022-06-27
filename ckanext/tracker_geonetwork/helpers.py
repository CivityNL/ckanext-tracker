import re
import urlparse

from ckanext.tracker.classes.helpers import link_is_enabled
from worker.geonetwork.rest import GeoNetworkRestApi
import logging

logging.basicConfig()
log = logging.getLogger(__name__)

DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

REGEX_IDENTIFIER = re.compile('(?<=<dc:identifier>)(.+)(?=<\/dc:identifier>)')
REGEX_NEXT_RECORD = re.compile('(?<=nextRecord=")([0-9]+)(?=")')
GEONETWORK_METADATA_LIST = []


def set_dict_elements(resource_dict, geonetwork_url):
    parameters = urlparse.urlparse(geonetwork_url)
    output_url = parameters.scheme + '://' + parameters.hostname
    if parameters.port is not None:
        output_url += ':' + str(parameters.port)
    output_url += parameters.path + '/geonetwork/srv/dut/catalog.search#/metadata/' + resource_dict[
        'id']
    resource_dict["geonetwork_url"] = output_url


def _before_show(resource_dict, organization):
    api = GeoNetworkRestApi(organization)
    record = api.read_record(resource_dict['id'])
    if record is not None:
        set_dict_elements(resource_dict, organization.geonetwork_url)


def get_records_url(limit=100, offset=1):
    return 'csw?request=GetRecords&service=CSW&version=2.0.2&typeNames=csw%3ARecord&elementsetname=summary&maxRecords={limit}&outputSchema=csw:Record&resultType=results&startPosition={offset}'. \
        format(limit=limit, offset=offset)


def get_records_and_nextrecord(api, offset=1):
    data = None
    records = []
    nextRecord = 0
    try:
        data = api.get('geonetwork/srv/eng', get_records_url(offset=offset))
    except:
        pass
        # log.debug("something went wrong with the GetRecords from {}".format(api.url))
    if data is not None:
        records = REGEX_IDENTIFIER.findall(data)
        nextRecordSearch = REGEX_NEXT_RECORD.search(data)
        nextRecord = int(nextRecordSearch.group(0))
    return records, nextRecord


def geonetwork_link_is_enabled(pkg_dict):
    return link_is_enabled(pkg_dict, 'geonetwork_link_enabled')


def should_publish_to_geonetwork(configuration, package, resource):
    '''
    multiple criteria to be met in order to publish to geoserver
    '''
    if not geonetwork_link_is_enabled(package):
        log.debug('should_publish is False because geonetwork_link_is_enabled is FALSE')
        return False
    if not resource_has_geoserver_metadata_populated(configuration, resource):
        log.debug('should_publish is False because resource_has_geoserver_metadata_populated is FALSE')
        return False
    return True


def should_unpublish_from_geonetwork(configuration, package, resource):
    if not geonetwork_link_is_enabled(package):
        log.debug('should_UNpublish is True because geonetwork_link_is_enabled is FALSE')
        return False
    if resource_has_geoserver_metadata_populated(configuration, resource):
        log.debug('should_UNpublish is True because resource_has_geoserver_metadata_populated is FALSE')
        return False
    log.debug('should_UNpublish is True')
    return True


def resource_has_geoserver_metadata_populated(configuration, resource):
    '''
    Check that all the geoserver related metadata exist and have values
    '''
    geoserver_resource_metadata_dict = [metadata.strip() for metadata in
                                        configuration.geoserver_resource_metadata.split(',')]
    for field in geoserver_resource_metadata_dict:
        if not field in resource.keys():
            return False
        if field in resource.keys() and not resource[field]:
            return False
    return True
