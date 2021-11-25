import os.path

from calibre.srv.routes import endpoint, json

@endpoint('/dshelper/status/{job_id}', types={'job_id': int}, auth_required=True, postprocess=json)
def dshelper_status(ctx, rd, job_id):
    job_status = ctx.job_status(job_id)
    return job_status

@endpoint('/dshelper/configuration', auth_required=True, postprocess=json)
def dshelper_configuration(ctx, rd):
    result = {}

    try:
        from calibre_plugins.count_pages.config import (plugin_prefs, get_library_config)
        count_pages_prefs = {"plugin_prefs": plugin_prefs}

        # from calibre.customize.ui import find_plugin
        # plugin = find_plugin('Count Pages')
        # db = plugin.actual_plugin_.gui.current_db
        # print("plugin db %s" % str(db.library_id))
        # for p in db:
        #     print("p db %s" % str(p))

        # from calibre.gui2.ui import get_gui
        # gui = get_gui()
        # print("gui %s" % str(gui))

        # from calibre.gui2.main import prefs
        # print("prefs %s" % str(prefs))
        
        # library_path = prefs['library_path']
        # print("library_path %s" % str(library_path))

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

        count_pages_prefs['library_config'] = library_configs

        result['count_pages_prefs'] = count_pages_prefs

    except ImportError:
        pass

    return result
    