# encoding: utf-8

from ckan.plugins.interfaces import Interface


class IOgr(Interface):
    """
    This interface is basically a placeholder/replacement of the IDataPusher and/or IXloader

    The IOgr interface allows plugin authors to receive notifications
    before and after a resource is submitted to the datapusher service, as
    well as determining whether a resource should be submitted in can_upload

    The before_submit function, when implemented
    """

    def can_upload(self, context, resource_dict, dataset_dict):
        """ Before a resource has been successfully upload to the datastore
        this method will be called with the resource dictionary and the
        package dictionary for this resource.

        :param context: The context within which the upload happened
        :param resource_dict: The dict represenstaion of the resource that was
            successfully uploaded to the datastore
        :param dataset_dict: The dict represenstation of the dataset containing
            the resource that was uploaded
        """
        pass

    def after_upload(self, context, resource_dict, dataset_dict):
        """ After a resource has been successfully upload to the datastore
        this method will be called with the resource dictionary and the
        package dictionary for this resource.

        :param context: The context within which the upload happened
        :param resource_dict: The dict represenstaion of the resource that was
            successfully uploaded to the datastore
        :param dataset_dict: The dict represenstation of the dataset containing
            the resource that was uploaded
        """
        pass