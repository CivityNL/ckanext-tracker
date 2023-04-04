import logging
from ckan.plugins import toolkit

log = logging.getLogger(__name__)


def get_show(object_type, object_id):
    return toolkit.get_action('{}_show'.format(object_type))({'ignore_auth': True}, {'id': object_id})


class TrackerContext(object):

    def __init__(self, package_id=None):
        super(TrackerContext, self).__init__()
        self._before_package = None
        self._after_package = None
        self._depth = 0
        self.before(package_id)

    def before(self, package_id):
        if package_id is not None:
            self._before_package = get_show('package', package_id)

    def after(self, package_id):
        if package_id is not None:
            self._after_package = get_show('package', package_id)

    def before_package(self):
        return self._before_package

    def after_package(self):
        return self._after_package

    def enter(self):
        self._depth = self._depth + 1

    def exit(self):
        self._depth = self._depth - 1

    def level(self):
        return self._depth == 0
