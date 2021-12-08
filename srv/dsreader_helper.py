import os.path
import copy

from calibre.srv.routes import endpoint, json

@endpoint('/dshelper/status/{job_id}', types={'job_id': int}, auth_required=True, postprocess=json)
def dshelper_status(ctx, rd, job_id):
    job_status = ctx.job_status(job_id)
    return job_status

@endpoint('/dshelper/configuration', auth_required=True, postprocess=json)
def dshelper_configuration(ctx, rd):
    result = {}

    try:
        result['dsreader_helper_prefs'] = get_dsreader_helper_prefs()
    except ImportError:
        pass

    try:
        result['count_pages_prefs'] = get_count_pages_prefs()
    except ImportError:
        pass

    try:
        result['goodreads_sync_prefs'] = get_goodreads_sync_prefs()
    except ImportError:
        pass

    try:
        result['reading_position_prefs'] = get_reading_position_prefs()
    except ImportError:
        pass

    return result

def get_dsreader_helper_prefs():
    prefs = {}
    from calibre_plugins.dsreader_helper.config import (plugin_prefs)
    prefs["plugin_prefs"] = copy.deepcopy(plugin_prefs)

    return prefs

def get_count_pages_prefs():
    prefs = {}
    from calibre_plugins.count_pages.config import (plugin_prefs, get_library_config)
    prefs["plugin_prefs"] = copy.deepcopy(plugin_prefs)

    from calibre.gui2 import gui_prefs
    gprefs = gui_prefs()
    # print("library_usage_stats %s" % str(gprefs['library_usage_stats']))

    library_configs = {}
    from calibre.db.legacy import LibraryDatabase
    for library_path in gprefs['library_usage_stats']:
        db = LibraryDatabase(library_path, read_only=True, is_second_db=True)
        library_config = get_library_config(db)
        print("library_config %s" % str(library_config))
        db.close()
        library_name = os.path.basename(library_path)
        library_configs[library_name] = library_config

    prefs['library_config'] = library_configs

    return prefs

def get_goodreads_sync_prefs():
    prefs = {}
    from calibre_plugins.goodreads_sync.config import (plugin_prefs)
    prefs["plugin_prefs"] = copy.deepcopy(plugin_prefs)

    # remove sensitive info
    if 'Goodreads' in prefs["plugin_prefs"]:
        prefs["plugin_prefs"]['Goodreads'].pop('devkeySecret', None)
        prefs["plugin_prefs"]['Goodreads'].pop('devkeyToken', None)
    if 'Users' in prefs["plugin_prefs"]:
        for profile in prefs["plugin_prefs"]['Users']:
            prefs["plugin_prefs"]['Users'][profile].pop('userId', None)
            prefs["plugin_prefs"]['Users'][profile].pop('userSecret', None)
            prefs["plugin_prefs"]['Users'][profile].pop('userToken', None)

    return prefs

def get_reading_position_prefs():
    prefs = {}
    from calibre_plugins.dsreader_helper.config import (get_library_reading_position_columns, get_library_reading_position_options)
    from calibre_plugins.dsreader_helper.config import PREFS_KEY_READING_POSITION_COLUMNS, PREFS_KEY_READING_POSITION_OPTIONS

    from calibre.gui2 import gui_prefs
    gprefs = gui_prefs()
    # print("library_usage_stats %s" % str(gprefs['library_usage_stats']))

    library_configs = {}
    from calibre.db.legacy import LibraryDatabase
    for library_path in gprefs['library_usage_stats']:
        db = LibraryDatabase(library_path, read_only=True, is_second_db=True)
        library_options = get_library_reading_position_options(db)
        library_columns = get_library_reading_position_columns(db)
        db.close()
        library_name = os.path.basename(library_path)
        library_configs[library_name] = {
            PREFS_KEY_READING_POSITION_COLUMNS: library_columns,
            PREFS_KEY_READING_POSITION_OPTIONS: library_options
        }

    prefs['library_config'] = library_configs

    return prefs
