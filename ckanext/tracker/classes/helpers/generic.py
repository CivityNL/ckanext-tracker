import re
from redis import Redis
import logging
import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as toolkit

log = logging.getLogger(__name__)


def set_connection():
    """
    This function will get the Redis connection information from the configuration and initialize a
    Redis connection based on the host and port
    :return: Redis connection
    """
    redis_url = toolkit.config.get('ckan.redis.url', 'redis://localhost:6379/0')
    m = re.match(r'.+(?<=:\/\/)(.+)(?=:):(.+)(?=\/)', redis_url)
    redis_host = m.group(1)
    redis_port = int(m.group(2))
    return Redis(redis_host, redis_port)


def get_user_apikey(user_id, target='source'):
    """
    This function will get the apikey for a specific user
    :return: apikey
    """
    try:
        if not user_id:
            return None
        user = model.User.get(user_id)
        if user:
            return user.apikey
    except:
        return None
    return None


def get_action_data(action, context, parameters):
    """
    This method is a wrapper around the toolkit.get_action which will check for any ActionErrors
    and if so will return a None object instead
    @param action:      action to perform
    @param context:     context for the action
    @param parameters:  specific parameters for the action
    @return:            either the result of the toolkit.get_action or None in case of an ActionError
    """
    action_data = None
    try:
        action_data = toolkit.get_action(action)(context, parameters)
    except logic.ActionError as actionError:
        pass
    return action_data


def link_is_enabled(data_dict, link_field_name):
    return link_field_name in data_dict and data_dict.get(link_field_name, None) == "True"


def raise_not_implemented_error(name):
    raise NotImplementedError("{} :: This method needs to be implemented to specify what should happen when and how.".format(
        name
    ))