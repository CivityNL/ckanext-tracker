# ckanext-tracker

This extension has been build as a wrapper around the core CKAN flow to 'track' changes in either packages and/or resources and to trigger actions based on those changes. The reason why this extension is necessary stems from the implementation of the `package_update` (and related actions) when not only updating the package itself, but also any resources within the package.

In general this extension relies on Redis to execute jobs based on changes on queues and return feedback using the `TaskStatus` model in CKAN.

The core of this extension is located in `./ckanext/tracker_base` which contains the building blocks which are used in the actual plugins. These building blocks can be seperated in 2 categories:

1. Tracking: the class `BaseTrackerPlugin` (and its child class `PackageResourceTrackerPlugin`) and the class `TrackerContext` handle the actual tracking of changes in CKAN objects.
2. Integration: the classes `TrackerBackend` and `TrackerBackendModel`, the interface `ITracker` and the `_callback_hook` action/auth functions manage the integration of a specific tracker plugin into the CKAN ecosystem.

Although the logic of tracking is universal, the execution is dependent on code from the `workers` extension, which gives a means to handle all types similar without any additional configuration handling or method mapping from the tracking side.

## BaseTrackerPlugin

### Properties

- `queue_name` (type: `str`): the name of the Redis queue used by an implementation. If `None` defaults to the name of the plugin.
- `configuration` (type: `Configuration`): the name of the Redis queue used by an implementation. If `None` defaults to the name of the plugin.
- `worker` (type: `WorkerWrapper`): which worker will be used for this implementation. Required.
- `redis_connection` (type: `Redis`): which worker will be used for this implementation. Required.
- `mapper` (type: `Mapper`): which mapper should be used to convert a given entity to it's harmonized form

- `badge_title` (type: `str`): text shown in the badge
- `show_ui` (type: `bool`, default: `True`): should this tracker be shown in the UI of the tracker plugin
- `show_badge` (type: `bool`, default: `False`): should the badge be shown (will be `False` when no `badge_title` is given)

### Configuration

As this is a generic implementation, most configuration options are per implementation

Tracker UI related (also see the [tracker](#ui-tracker) plugin)
- `ckanext.{plugin}.badge_title`: see `badge_title` in the Properties section above
- `ckanext.{plugin}.show_ui`: see `show_ui` in the Properties section above
- `ckanext.{plugin}.show_badge`: see `show_badge` in the Properties section above
Address information (see workers for more information)
- `ckanext.{plugin}.address` (default: `Handelsweg 6`)
- `ckanext.{plugin}.address.city` (default: `Zeist`):
- `ckanext.{plugin}.address.country` (default: `the Netherlands`):
- `ckanext.{plugin}.address.phone` (default: `+31 30 697 32 86`):
- `ckanext.{plugin}.address.state` (default: `Utrecht`):
- `ckanext.{plugin}.address.type` (default: `electronic`):
- `ckanext.{plugin}.address.zip_code` (default: `3707 NH`)
OGR: Command to use for `ogr2ogr` (also see the [tracker_ogr](#ogr-trackerogr) plugin)
- `ckanext.{plugin}.command.ogr2ogr` (default: `ogr2ogr`)
Contact information (see workers for more information)
- `ckanext.{plugin}.contact.email` (default: `support@civity.nl`)
- `ckanext.{plugin}.contact.organization` (default: `Civity`)
- `ckanext.{plugin}.contact.person` (default: `Mathieu Ronkes Agerbeek`)
- `ckanext.{plugin}.contact.position` (default: `Support engineer`)
- `ckanext.{plugin}.contact.url` (default: `https://civity.nl`)
GeoNetwork: URL and default license  (also see the [tracker_geonetwork](#geonetwork-trackergeonetwork) plugin)
- `ckanext.{plugin}.geonetwork.url` (optional):
- `ckanext.{plugin}.geonetwork.default_license_url` (optional):
URL and other information for GeoServer  (also see the [tracker_geoserver](#geoserver-trackergeoserver) plugin)
- `ckanext.{plugin}.geoserver.url` (optional):
- `ckanext.{plugin}.geoserver.layer_prefix` (optional):
- `ckanext.{plugin}.geoserver.resource_metadata` (optional):
Redis
- `ckanext.{plugin}.redis_job_timeout` (default: `180`):
- `ckanext.{plugin}.redis_job_result_ttl` (default: `500`):
- `ckanext.{plugin}.redis_job_ttl` (optional):
CKAN: URL and other information (also see the [tracker_ckantockan](#ckan-trackerckantockan) plugin and it's derivatives)
- `ckanext.{plugin}.remote_ckan_host`:
- `ckanext.{plugin}.remote_ckan_org`:
- `ckanext.{plugin}.remote_user_api_key`:
- `ckanext.{plugin}.remote_ckan_user`:

## PackageResourceTrackerPlugin

### Properties

- `separate_tracking` (type: `bool`, default: `False`): Should packages and resources be tracked separately (e.g. is a change in a resource something different than a change in a package)
- `ignore_packages` (type: `bool`, default: `False`): ignore any changes to packages
- `ignore_resources` (type: `bool`, default: `False`): ignore any changes to resources
- `include_resource_fields` (type: `list`, default: `None`): focus on any changes in the resource based on the given fields
- `exclude_resource_fields` (type: `list`, default: `None`): ignore any changes in the resource based on the given fields
- `include_package_fields` (type: `list`, default: `None`): focus on any changes in the package based on the given fields
- `exclude_package_fields` (type: `list`, default: `None`): ignore any changes in the package based on the given fields

## Plugins

With the basics out of the way, the actual (currently) usable plugins will be addressed as they appear in the `setup.py`. In general for each plugin the main purpose will be described as well as any additions to CKAN's Action API, Template Helpers, and new/updated UI pages/snippets/endpoints.

>`Callback action`
>
> Description
>
>Parameters:
: `id` (`string`) - the id of the resource
: `state` (`string`) - either `created`, `updated` or `deleted`

> Authorization:
: Only allowed by users that are also allowed to update the resource with the given id

>Returns:
: Nothing

>Return type:
: Nothing


Description:
        Tony J. (Tibs) Ibbs,
        David Goodger
        (and sundry other good-natured folks)
    :Parameters:
        - `id` (`string`) - the id of the resource
        - `state` (`string`) - either `created`, `updated` or `deleted`
    :Returns: Nothing.
    :Authorization: Only allowed by users that are also allowed to update the resource with the given id

### UI (`tracker`)
[tracker](#ui-tracker)

This plugin (tries) to give the users an interface to interact with the trackers working from behind the scenes. As those actions sometimes have to wait until they get executed, feedback is required to give a sense if something is happening or not.

#### Template Helpers

>`get_trackers()`
>
> Description
>
>Parameters:
: `id` (`string`) - the id of the resource
: `state` (`string`) - either `created`, `updated` or `deleted`

> Authorization:
: Only allowed by users that are also allowed to update the resource with the given id

>Returns:
: Nothing

>Return type:
: Nothing

---

>`get_tracker_badges()`
>
> Description
>
>Parameters:
: `id` (`string`) - the id of the resource
: `state` (`string`) - either `created`, `updated` or `deleted`

> Authorization:
: Only allowed by users that are also allowed to update the resource with the given id

>Returns:
: Nothing

>Return type:
: Nothing   

---

>`get_tracker_activities()`
>
> Description
>
>Parameters:
: `id` (`string`) - the id of the resource
: `state` (`string`) - either `created`, `updated` or `deleted`

> Authorization:
: Only allowed by users that are also allowed to update the resource with the given id

>Returns:
: Nothing

>Return type:
: Nothing 

---

>`get_tracker_activities_stream()`
>
> Description
>
>Parameters:
: `id` (`string`) - the id of the resource
: `state` (`string`) - either `created`, `updated` or `deleted`

> Authorization:
: Only allowed by users that are also allowed to update the resource with the given id

>Returns:
: Nothing

>Return type:
: Nothing 

---

>`get_tracker_queues()`
>
> Description
>
>Parameters:
: `id` (`string`) - the id of the resource
: `state` (`string`) - either `created`, `updated` or `deleted`

> Authorization:
: Only allowed by users that are also allowed to update the resource with the given id

>Returns:
: Nothing

>Return type:
: Nothing 

---

>`hash()`
>
> Description
>
>Parameters:
: `id` (`string`) - the id of the resource
: `state` (`string`) - either `created`, `updated` or `deleted`

> Authorization:
: Only allowed by users that are also allowed to update the resource with the given id

>Returns:
: Nothing

>Return type:
: Nothing 

#### Pages

- ##### [base.html](/ckanext/tracker/templates/base.html): [Extends] Adds the CSS asset

Admin:

- ##### [admin/base.html](/ckanext/tracker/templates/admin/base.html): [Extends] Adds a navigation option to the primary navigation to `/ckan-admin/trackers`
- ##### [admin/trackers.html](/ckanext/tracker/templates/admin/trackers.html): [New] This page shows the information of all registered trackers. The information is split up in two tables: the first shows the information by (Redis) queue in terms of number of workers/jobs. The second table contains the information by tracker in terms of number of jobs. This division has been made as multiple trackers could use the same queue. 

Package:

- ##### [package/edit_base.html](/ckanext/tracker/templates/package/edit_base.html): [Extends] Adds a navigation option to the primary navigation to `/dataset/<id>/trackers`
- ##### [package/read.html](/ckanext/tracker/templates/package/read.html): [Extends] Adds a row of badges at the end of the page heading based on the `get_tracker_badges` template helper function for that package

Resource:

- ##### [package/resource_edit_base.html](/ckanext/tracker/templates/package/resource_edit_base.html): [Extends] Adds a navigation option to the primary navigation to `/dataset/<id>/resource/<resource_id>/trackers`
- ##### [package/resource_read.html](/ckanext/tracker/templates/package/resource_read.html): [Extends] Adds a row of badges at the end of the page heading based on the `get_tracker_badges` template helper function for that resource 

Tracker [New]

- ##### [tracker/package_data.html](/ckanext/tracker/templates/tracker/package_data.html): [New (extends `package/edit_base.html`)] Shows the tracker information available for the current package using the `get_trackers`, `get_tracker_statuses`, and `get_tracker_activities_stream` template helper functions for that package in combination with the 'tracker/snippets/job_overview.html' and 'tracker/snippets/job_stream.html' snippets
- ##### [tracker/resource_data.html](/ckanext/tracker/templates/package/resource_read.html): [New (extends `package/resource_edit_base.html`)] Same as [above](#trackerpackagedatahtml) except now on resource level

#### Snippets

##### [tracker/snippets/job_overview.html](/ckanext/tracker/templates/tracker/snippets/job_overview.html)
> [New (extends `package/resource_edit_base.html`)] Same as [above](#trackerpackagedatahtml) except now on resource level
> 
> Usage: `{% snippet 'tracker/snippets/job_overview.html', statuses=statusses %}`

##### [tracker/snippets/job_stream.html](/ckanext/tracker/templates/tracker/snippets/job_stream.html)
> [New (extends `package/resource_edit_base.html`)] Same as [above](#trackerpackagedatahtml) except now on resource level



#### Endpoints

- ##### `/ckan-admin/trackers`: Will render [admin/base.html](#adminbasehtml)
- ##### `/dataset/<id>/trackers`: Will render [tracker/package_data.html](#trackerpackagedatahtml)
- ##### `/dataset/<id>/resource/<resource_id>/trackers`: Will render [tracker/resource_data.html](#trackerresourcedatahtml)

### CKAN (`tracker_ckantockan`)
[tracker_ckantockan](#ckan-trackerckantockan)

### Geonetwork (`tracker_geonetwork`)
[tracker_geonetwork](#geonetwork-trackergeonetwork)

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

### Geoserver (`tracker_geoserver`)
[tracker_geoserver](#geoserver-trackergeoserver)

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

### OGR (`tracker_ogr`)
[tracker_ogr](#ogr-trackerogr)

#### Actions
- `ogr_callback_hook`: ogr_callback_hook
#### Templates
- `ogr/resource_data.html`: TrackerBackend.get_trackers,
- `package/resource_edit_base.html`: helpers.get_tracker_activities_stream,
#### Endpoints
- `/dataset/{id}/resource_data/{resource_id}`
- `/ogr/dump/{resource_id}`

dfsgdsfgdsfg

| Syntax | Description |
| ----------- | ----------- |
| Header | Title |
| Paragraph | Text |



``
{
  "firstName": "John",
  "lastName": "Smith",
  "age": 25
}
``

Here's a sentence with a footnote. [^1]

[^1]: This is the footnote.

term
: definition

~~The world is flat.~~

- [x] Write the press release
- [ ] Update the website
- [ ] Contact the media

That is so funny! :joy:

I need to highlight these ==very important words==.

H~2~O

X^2^









dsfgsdfgsdfgsdfgdfg