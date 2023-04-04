import logging

from ckanext.tracker_base.model import TrackerBackendModel

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
        cls.add_tracker_model(cls.create_tracker_model(tracker))

    @classmethod
    def get_trackers(cls):
        """
        Simple getter for all registered TrackerBackendModels
        """
        return cls.trackers

    @classmethod
    def get_tracker(cls, name):
        """
        Simple getter for a specific TrackerBackendModel
        """
        result = None
        for tracker in cls.trackers:
            if tracker.name == name:
                result = tracker
                break
        return result

    @classmethod
    def create_tracker_model(cls, tracker):
        """
        Simple method to convert a BaseTrackerPlugin implementation into a TrackerBackendModel
        """
        return TrackerBackendModel(
            name=tracker.name,
            queue=tracker.get_queue_name(),
            badge_title=tracker.get_badge_title(),
            show_badge=tracker.get_show_badge(),
            show_ui=tracker.get_show_ui()
        )

    @classmethod
    def add_tracker_model(cls, tracker_model):
        """
        Simple add method which also checks if a specific TrackerBackendModel isn't already there
        """
        if len(cls.trackers) == 0:
            cls.trackers.append(tracker_model)
            log.info("tracker {} is successfully registered".format(
                tracker_model.name
            ))
        else:
            exists = False
            for tracker in cls.trackers:
                if tracker == tracker_model:
                    exists = True
                    break
            if not exists:
                cls.trackers.append(tracker_model)
                log.info("tracker {} is successfully registered".format(
                    tracker_model.name
                ))
            else:
                log.info("tracker {} is already registered".format(
                    tracker_model.name
                ))
