import logging
from ckanext.tracker_ckantockan.helpers import link_is_enabled

log = logging.getLogger(__name__)


def should_link_to_donl(pkg_dict):
    return link_is_enabled(pkg_dict, 'donl_link_enabled') and not link_is_enabled(pkg_dict, 'geonetwork_link_enabled')
