import ckanext.packagetracker.plugin as packagetracker
from worker.ckan_to_ckan import CkanToCkanWorkerWrapper

import logging
log = logging.getLogger(__name__)


class Packagetracker_CkantockanPlugin(packagetracker.PackagetrackerPlugin):

    worker = CkanToCkanWorkerWrapper()

    def do_delete(self):
        return self.do_purge()
