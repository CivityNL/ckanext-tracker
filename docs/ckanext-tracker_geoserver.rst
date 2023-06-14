=================================
ckanext-resourcetracker_geoserver
=================================

before_show
***********
Populate resource's metadata corresponding to connected Geoserver machine:

- ows_url
- ows_layer
- wms_url
- wfs_url

This will result in an 'on-the-fly' creation of the WMS/WFS endpoints of the accessed resource.

The above metadata are required for properly displaying the Portal's map visualizations.

Building WMS/WFS endpoints
**************************
URL used to access Geoserver is assigned to a DNS entry, forwarding the path from::

     http://{GEOSERVER_IP}/geoserver

to::

   http://{CKAN_INSTANCE_NAME}/geoserver



WMS/WFS endpoints though will make use of the geoserver URL plus the workspace (Geoserver Virtual Service filtered by workspace)::

   http://{CKAN_INSTANCE_NAME}/geoserver/{CKAN_INSTANCE_WORKSPACE}/{SERVICE_PARAMS}


The above structure, followed by the service parameters will result in accessing the full service.
For example, when trying to access a WMS layer from a GIS software, you will come up with a list
of all available WMS layers of the workspace.
In order to restrict access 'per layer' rather than 'per workspace', the endpoint must be re-structured like ::

   http://{CKAN_INSTANCE_NAME}/geoserver/{CKAN_INSTANCE_WORKSPACE}/{LAYER_NAME}/{SERVICE_PARAMS}


Defining the layer name between the workpace declaration and service parameters minimizes access to only the requested layer (Geoserver Virtual Service filtered by layer).

Official Geoserver document `here <https://docs.geoserver.org/stable/en/user/configuration/virtual-services.html>`_