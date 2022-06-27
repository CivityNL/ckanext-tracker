from ckan.logic import get_or_bust as _get_or_bust, ValidationError
import ckan.plugins as plugins
import logging

log = logging.getLogger(__name__)


def _callback_hook(context, data_dict, interface):
    log.debug("_callback_hook")
    resource_id = _get_or_bust(data_dict, 'id')
    state = _get_or_bust(data_dict, 'state')

    if state not in ['created', 'updated', 'deleted']:
        raise ValidationError("state should either be 'created', 'updated' or 'deleted', not '{}'".format(state))

    res_dict = plugins.toolkit.get_action('resource_show')(context, {'id': resource_id})
    pkg_dict = plugins.toolkit.get_action('package_show')(context, {'id': res_dict['package_id']})

    for plugin in plugins.PluginImplementations(interface):
        log.info('running {} implementation of callback for {}'.format(interface.__name__, plugin))
        plugin.callback(context, state, res_dict, pkg_dict)
