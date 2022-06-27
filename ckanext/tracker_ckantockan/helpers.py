def is_private(pkg_dict):
    return 'private' in pkg_dict and pkg_dict.get("private")


def is_draft(pkg_dict):
    return 'state' in pkg_dict and pkg_dict.get("state") == 'draft'


def has_id(data_dict):
    return 'id' in data_dict and data_dict.get("id") is not None


def link_is_enabled(data_dict, link_field_name):
    return link_field_name in data_dict and data_dict.get(link_field_name) == "True"
