import ckan.plugins as plugins
import ckan.logic as logic

_get_or_bust = logic.get_or_bust


def _callback_hook(context, data_dict):
    resource_id = _get_or_bust(data_dict, 'id')
    user = context.get('user')
    authorized = plugins.toolkit.check_access('resource_update', context, data_dict)

    if not authorized:
        return {
            'success': False,
            'msg': plugins.toolkit._('User {0} not authorized to update resource {1}'.format(str(user), resource_id))
        }
    else:
        return {'success': True}

