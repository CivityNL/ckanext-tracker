import ckanext.datastoretracker.plugin as datastoretracker


class Datastoretracker_XlsToCsvPlugin(datastoretracker.DatastoretrackerPlugin):
    queue_name = 'datastore_xlstocsv'
