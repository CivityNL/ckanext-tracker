from ckan.plugins import toolkit


def _callback_hook(context, data_dict):
    resource_id = toolkit.get_or_bust(data_dict, 'id')
    user = context.get('user')
    authorized = toolkit.check_access('resource_update', context, data_dict)

    if not authorized:
        return {
            'success': False,
            'msg': toolkit._('User {0} not authorized to update resource {1}'.format(str(user), resource_id))
        }
    else:
        return {'success': True}
