# Extension `ckanext-tracker`

In general this extension has been developed to have a more specific way of tracking/monitoring events happening in the CKAN flow of creating/updating/deleting/purging packages and/or resources and to take actions (either within the flow itself and/or by using jobs).
For this to work correctly an attempt has been made to fix issues with mixed actions in a package action (e.g. creating both resources and a package in the same call) or similar combinations being it updates or deletions.
This extension coexists with a list of 'workers': pieces of code that always have the same methods.

# Implementation

## BaseTrackerPlugin

This is a basic implementation containing all the logic in regards to communication towards Redis for the jobs and the TrackerBackend. Also makes sure the handling of the task_status objects is done correctly in case of exceptions and/or purging of entities.

### Properties

- `queue_name` (type: `str`): the name of the Redis queue used by an implementation. If `None` defaults to the name of the plugin.
- `worker` (type: `WorkerWrapper`): which worker will be used for this implementation. Required.
- `mapper` (type: `Mapper`): which mapper should be used to convert a given entity to it's harmonized form
- `badge_title` (type: `str`): text shown in the badge
- `show_ui` (type: `bool`, default: `True`): should this tracker be shown in the UI of the tracker plugin
- `show_badge` (type: `bool`, default: `False`): should the badge be shown (will be `False` when no `badge_title` is given)		

### Configuration

As this is a generic implementation, most configuration options are per implementation

#### Tracker UI related (also see the `tracker` plugin)
- `ckanext.{plugin}.badge_title`: see `badge_title` in the Properties section above
- `ckanext.{plugin}.show_ui`: see `show_ui` in the Properties section above
- `ckanext.{plugin}.show_badge`: see `show_badge` in the Properties section above
#### Address information (see workers for more information)
- `ckanext.{plugin}.address` (default: `Handelsweg 6`)
- `ckanext.{plugin}.address.city` (default: `Zeist`): 
- `ckanext.{plugin}.address.country` (default: `the Netherlands`): 
- `ckanext.{plugin}.address.phone` (default: `+31 30 697 32 86`):
- `ckanext.{plugin}.address.state` (default: `Utrecht`):
- `ckanext.{plugin}.address.type` (default: `electronic`):
- `ckanext.{plugin}.address.zip_code` (default: `3707 NH`)
#### Command to use for `ogr2ogr` (also see the `tracker_ogr` plugin)
- `ckanext.{plugin}.command.ogr2ogr` (default: `ogr2ogr`)
#### Contact information (see workers for more information)
- `ckanext.{plugin}.contact.email` (default: `support@civity.nl`)
- `ckanext.{plugin}.contact.organization` (default: `Civity`)
- `ckanext.{plugin}.contact.person` (default: `Mathieu Ronkes Agerbeek`)
- `ckanext.{plugin}.contact.position` (default: `Support engineer`)
- `ckanext.{plugin}.contact.url` (default: `https://civity.nl`)
#### URL and default license for GeoNetwork  (also see the `tracker_geonetwork` plugin)
- `ckanext.{plugin}.geonetwork.url` (optional):
- `ckanext.{plugin}.geonetwork.default_license_url` (optional):
#### URL and other information for GeoServer  (also see the `tracker_geoserver` plugin)
- `ckanext.{plugin}.geoserver.url` (optional): 
- `ckanext.{plugin}.geoserver.layer_prefix` (optional): 
- `ckanext.{plugin}.geoserver.resource_metadata` (optional): 
##### Redis
- `ckanext.{plugin}.redis_job_timeout` (default: `180`):
- `ckanext.{plugin}.redis_job_result_ttl` (default: `500`):
- `ckanext.{plugin}.redis_job_ttl` (optional):
#### URL and other information for GeoServer  (also see the `tracker_ckantockan` plugin and it's derivatives)
- `ckanext.{plugin}.remote_ckan_host`: 
- `ckanext.{plugin}.remote_ckan_org`: 
- `ckanext.{plugin}.remote_user_api_key`: 
- `ckanext.{plugin}.remote_ckan_user`: 
#### URL and other information for GeoServer  (also see the `tracker_geoserver` plugin)
- `ckanext.{plugin}.source_ckan_host` (default: value for `ckan.site_url`)
- `ckanext.{plugin}.source_ckan_org`: 
- `ckanext.{plugin}.source_ckan_user` (default: `automation`):


## PackageResourceTrackerPlugin (extends BaseTrackerPlugin, used by all plugins except tracker)
## TrackerBackend (tracker)

This class is a way to keep track off all TrackerPlugins running on a specific instance which is basically a glorified list of trackers and some methods to add (register) and retrieve added trackers

# Plugins

## `tracker` (a.k.a Tracker UI)

### Actions
This plugin does not introduce any new actions
### Template Helpers
- `get_trackers`: TrackerBackend.get_trackers,
- `get_tracker_badges`: helpers.get_tracker_badges,
- `get_tracker_statuses`: helpers.get_tracker_statuses,
- `get_tracker_activities`: helpers.get_tracker_activities,
- `get_tracker_activities_stream`: helpers.get_tracker_activities_stream,
- `get_tracker_queues`: helpers.get_tracker_queues,
- `hash`: helpers.hash
### Templates
- `admin/base.html`: TrackerBackend.get_trackers,
- `admin/trackers.html`: helpers.get_tracker_badges,
- `package/edit_base.html`: helpers.get_tracker_statuses,
- `package/read.html`: helpers.get_tracker_activities,
- `package/resource_edit_base.html`: helpers.get_tracker_activities_stream,
- `package/resource_read.html`: helpers.get_tracker_queues,
- `tracker/package_data.html`: helpers.hash
- `tracker/resource_data.html`: helpers.hash
### Snippets
- `tracker/snippets/job_details.html`: TrackerBackend.get_trackers,
- `tracker/snippets/job_overview.html`: TrackerBackend.get_trackers,
- `tracker/snippets/job_stream.html`: TrackerBackend.get_trackers
### Endpoints
- `/dataset/<id>/trackers`
- `/dataset/<id>/resource/<resource_id>/trackers`
- `/ckan-admin/trackers`
## tracker_ckantockan

### Actions
This plugin does not introduce any new template helpers
### Template Helpers
This plugin does not introduce any new template helpers
### Templates
This plugin does not introduce any new or changed templates
### Snippets
This plugin does not introduce any new snippets
### Endpoints
This plugin does not introduce any new endpoints

### tracker_ckantockan_donl

### tracker_ckantockan_oneckan

### tracker_ckantockan_oneckan_rotterdam
### tracker_ckantockan_oneckan_lidingo
## tracker_geonetwork

### Actions
- `geonetwork_callback_hook`: geonetwork_callback_hook
### Template Helpers
This plugin does not introduce any new template helpers
### Templates
- `package/resource_read.html`: helpers.get_tracker_queues
### Snippets
This plugin does not introduce any new snippets
### Endpoints
This plugin does not introduce any new endpoints

## tracker_geoserver

### Actions
- `geoserver_callback_hook`: geonetwork_callback_hook
### Template Helpers
This plugin does not introduce any new template helpers
### Templates
- `package/resource_read.html`: helpers.get_tracker_queues
### Snippets
This plugin does not introduce any new snippets
### Endpoints
This plugin does not introduce any new endpoints

## tracker_ogr (a.k.a XLoader/Datapusher 2.0)

### Actions
- `ogr_callback_hook`: ogr_callback_hook
### Template Helpers
This plugin does not introduce any new template helpers
### Templates
- `ogr/resource_data.html`: TrackerBackend.get_trackers,
- `package/resource_edit_base.html`: helpers.get_tracker_activities_stream,
### Snippets
This plugin does not introduce any new snippets
### Endpoints
- `/dataset/{id}/resource_data/{resource_id}`
- `/ogr/dump/{resource_id}`