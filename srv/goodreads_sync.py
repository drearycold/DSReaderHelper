from calibre.srv.routes import endpoint, json

from calibre_plugins.dsreader_helper.config import plugin_prefs, STORE_NAME, KEY_GOODREADS_SYNC_ENABLED
from calibre.customize.ui import find_plugin

@endpoint('/dshelper/grsync/get_profile_names', auth_required=True, postprocess=json)
def grsync_get_profile_names(ctx, rd):
    # import traceback
    # traceback.print_stack()

    enabled = plugin_prefs[STORE_NAME].get(KEY_GOODREADS_SYNC_ENABLED, False)
    if not enabled:
        return ['__GYSYNC_NOT_ENABLED__']
    try:
        grsync = find_plugin("Goodreads Sync")
        if grsync and grsync.actual_plugin_:
            print("grsync %s %s" % (str(grsync), str(grsync.actual_plugin_)))
            users = grsync.actual_plugin_.users
        else:
            import calibre_plugins.goodreads_sync.config as cfg
            users = cfg.plugin_prefs[cfg.STORE_USERS]
        
        print("GRSYNC %s" % str(users))
    except ImportError:
        print("GRSYNC NOT FOUND")
        users = ['__GRSYNC_NOT_FOUND__']

    return [*users]

@endpoint('/dshelper/grsync/add_remove_book_to_shelf', auth_required=True)
def grsync_add_remove_book_to_shelf(ctx, rd):
    enabled = plugin_prefs[STORE_NAME].get(KEY_GOODREADS_SYNC_ENABLED, False)
    if not enabled:
        return '-1'

    goodreads_id = rd.query.get('goodreads_id', None)
    if goodreads_id is None:
        return b'missing goodreads_id'

    profile_name = rd.query.get('profile_name', None)
    if profile_name is None:
        return b'missing profile_name'

    shelf_name = rd.query.get('shelf_name', None)
    if shelf_name is None:
        return b'missing shelf_name'

    action = rd.query.get('action', None)
    if action is None:
        return b'missing action'

    ret = ctx.start_job(
            'Modify Book Shelf',
            'calibre_plugins.dsreader_helper.jobs', 
            'grsync_add_remove_book_to_shelf', 
            (goodreads_id, profile_name, shelf_name, action)
        )

    return str(ret)

@endpoint('/dshelper/grsync/update_reading_progress', auth_required=True)
def grsync_update_reading_progress(ctx, rd):
    enabled = plugin_prefs[STORE_NAME].get(KEY_GOODREADS_SYNC_ENABLED, False)
    if not enabled:
        return '-1'

    goodreads_id = rd.query.get('goodreads_id', None)
    if goodreads_id is None:
        return b'missing goodreads_id'

    percent = rd.query.get('percent', None)
    if percent is None:
        return b'missing percent'

    profile_name = rd.query.get('profile_name', None)
    if profile_name is None:
        return b'missing profile_name'

    ret = ctx.start_job(
            'Update Reading Progress',
            'calibre_plugins.dsreader_helper.jobs', 
            'grsync_update_reading_progress', 
            (goodreads_id, percent, profile_name)
        )

    return str(ret)
