# encoding: utf-8

from ckan.plugins.interfaces import Interface


class ITracker(Interface):

    def callback(self, context, state, resource_dict, dataset_dict):
        pass
