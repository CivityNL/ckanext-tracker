import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import ckanext.resourcetracker.plugin as resourcetracker


class Resourcetracker_CkantockanPlugin(resourcetracker.ResourcetrackerPlugin):

    queue_name = 'ckantockan'
