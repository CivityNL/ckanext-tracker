import logging

from ckanext.tracker.model import TrackerBackendModel

log = logging.getLogger(__name__)


class TrackerBackend:
    """
    This class is a way to keep track off all TrackerPlugins running on a specific instance which is basically a glorified
    list of trackers and some methods to add (register) and retrieve added trackers
    """

    def __init__(self):
        pass

    trackers = []

    @classmethod
    def register(cls, tracker):
        """
        This method will add a TrackerModel based on a BaseTrackerPlugin to the registry for every type it has
        @param tracker: BaseTrackerPlugin implementation
        """
        for type in tracker.get_types():
            cls.add_tracker_model(cls.create_tracker_model(tracker, type))

    @classmethod
    def get_trackers(cls):
        """
        Simple getter for all registered TrackerBackendModels
        """
        return cls.trackers

    @classmethod
    def get_tracker(cls, type, name):
        """
        Simple getter for a specific TrackerBackendModel
        """
        result = None
        for tracker in cls.trackers:
            if tracker.type == type and tracker.name == name:
                result = tracker
                break
        return result

    @classmethod
    def get_trackers_by_types(cls, types):
        """
        Simple getter which filters on types
        @param types: list of strings (if a string is passed it will assume you meant the get_trackers_by_type method)
        @return: list of TrackerBackendModels
        """
        if not isinstance(types, list):
            return cls.get_trackers_by_type(types)
        trackers_by_types = []
        for type in types:
            trackers_by_types = trackers_by_types + cls.get_trackers_by_type(type)
        return trackers_by_types

    @classmethod
    def get_trackers_by_type(cls, type):
        """
        Simple getter which filters on type
        @param type: string (if a list is passed it will assume you meant the get_trackers_by_types method)
        @return: list of TrackerBackendModels
        """
        if isinstance(type, list):
            return cls.get_trackers_by_types(type)
        trackers_by_type = []
        for tracker in cls.trackers:
            if tracker.type == type:
                trackers_by_type.append(tracker)
        return trackers_by_type

    @classmethod
    def create_tracker_model(cls, tracker, type):
        """
        Simple method to convert a BaseTrackerPlugin implementation into a TrackerBackendModel
        """
        upsert_method = None
        if type == 'package':
            upsert_method = tracker.get_worker().upsert_package
        elif type == 'resource':
            upsert_method = tracker.get_worker().upsert_resource
        return TrackerBackendModel(
            type=type,
            name=tracker.name,
            badge_title_method=tracker.get_badge_title,
            show_badge_method=tracker.get_show_badge,
            show_ui_method=tracker.get_show_ui,
            enqueue_method=tracker.put_on_a_queue,
            upsert_method=upsert_method
        )

    @classmethod
    def add_tracker_model(cls, tracker_model):
        """
        Simple add method which also checks if a specific TrackerBackendModel isn't already there
        """
        if len(cls.trackers) == 0:
            cls.trackers.append(tracker_model)
            log.info("tracker {} of type {} is successfully registered".format(
                tracker_model.name, tracker_model.type
            ))
        else:
            exists = False
            for tracker in cls.trackers:
                if tracker == tracker_model:
                    exists = True
                    break
            if not exists:
                cls.trackers.append(tracker_model)
                log.info("tracker {} of type {} is successfully registered".format(
                    tracker_model.name, tracker_model.type
                ))
            else:
                log.info("tracker {} of type {} is already registered".format(
                    tracker_model.name, tracker_model.type
                ))
