class TrackerBackendModel:
    """
    This is a simple model holding all information from a BaseTrackerPlugin instance which is used by the TrackerPlugin
    """

    def __init__(self, type, name, badge_title_method, show_badge_method, show_ui_method, enqueue_method, upsert_method):
        self.type = type
        self.name = name
        self.badge_title_method = badge_title_method
        self.show_badge_method = show_badge_method
        self.show_ui_method = show_ui_method
        self.enqueue_method = enqueue_method
        self.upsert_method = upsert_method

    def __eq__(self, other):
        if isinstance(other, TrackerBackendModel):
            return self.name == other.name and self.type == other.type
        return False
