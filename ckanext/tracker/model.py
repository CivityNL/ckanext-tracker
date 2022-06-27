class TrackerBackendModel:
    """
    This is a simple model holding all information from a BaseTrackerPlugin instance which is used by the TrackerPlugin
    """

    def __init__(self, name, queue, badge_title, show_badge, show_ui):
        self.name = name
        self.queue = queue
        self.badge_title = badge_title
        self.show_badge = show_badge
        self.show_ui = show_ui

    def __eq__(self, other):
        if isinstance(other, TrackerBackendModel):
            return self.name == other.name
        return False
