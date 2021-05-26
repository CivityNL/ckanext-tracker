import ckanext.datastore.logic.auth as auth


def ogr_can_upload_hook(context, data_dict):
    return auth.datastore_auth(context, data_dict)


def ogr_after_upload_hook(context, data_dict):
    return auth.datastore_auth(context, data_dict)
