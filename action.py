#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2021, Drearycold <drearycold@gmail.com>'
__docformat__ = 'restructuredtext en'

import os, sys
from zipfile import ZipFile

from functools import partial
try:
    from PyQt5.Qt import QToolButton, QMenu
except ImportError:
    from PyQt4.Qt import QToolButton, QMenu

from calibre.gui2.actions import InterfaceAction

import calibre_plugins.dsreader_helper.config as cfg
from calibre_plugins.dsreader_helper.common_utils import (set_plugin_icon_resources, get_icon, create_menu_action_unique)

try:
    load_translations()
except NameError:
    pass # load_translations() added in calibre 1.9

class DSReaderHelperAction(InterfaceAction):

    name = 'DSReader Helper'
    # Create our top-level menu/toolbar action (text, icon_path, tooltip, keyboard shortcut)
    action_spec = ('DSReader Helper', None, _('Helper Plugin for D.S.Reader iOS App\n'
                                          'to automate various refreshing actions'), ())
    # popup_type = QToolButton.MenuButtonPopup
    action_type = 'current'
    # dont_add_to = frozenset(['context-menu-device'])

    def genesis(self):
        self.menu = QMenu(self.gui)
        # Read the plugin icons and store for potential sharing with the config widget
        icon_resources = self.load_resources(cfg.PLUGIN_ICONS)
        set_plugin_icon_resources(self.name, icon_resources)

        self.rebuild_menus()

        # Assign our menu to this action and an icon
        self.qaction.setMenu(self.menu)
        self.qaction.setIcon(get_icon(cfg.PLUGIN_ICONS[0]))
        self.qaction.triggered.connect(self.toolbar_triggered)
        self.menu.aboutToShow.connect(self.about_to_show_menu)

        # Used to store callback details when called from another plugin.
        self.plugin_callback = None

        # from calibre.srv.embedded import Server
        from calibre_plugins.dsreader_helper.srv.server import Server
        from calibre.gui2 import Dispatcher
        self.server = Server(self.gui.library_broker, Dispatcher(self.handle_changes_from_server))
        print('server %s' % str(self.server))
        self.server.start()
        print('server current_thread %s' % str(self.server.current_thread))

        self.rebuild_dict_builders()
        # result_text = builder.mdx_lookup('dedication')
        # print('mdx result %s' % result_text)

    def handle_changes_from_server(self, library_path, change_event):
        print('Received server change event: {} for {}'.format(change_event, library_path))
        # if self.library_broker.is_gui_library(library_path):
        #     self.server_changes.put((library_path, change_event))
        #     self.server_change_notification_timer.start()

    def about_to_show_menu(self):
        self.rebuild_menus()

    def rebuild_menus(self):
        m = self.menu
        m.clear()
        create_menu_action_unique(self, m, _('&Customize plugin')+'...', 'dsreader.png',
                                  shortcut=False, triggered=self.show_configuration)
        self.gui.keyboard.finalize()

    def toolbar_triggered(self):
        self.show_configuration()

    def show_configuration(self):
        self.interface_action_base_plugin.do_user_config(self.gui)

    def rebuild_dict_builders(self):
        self.builders = {}
        c = cfg.plugin_prefs[cfg.STORE_NAME]

        import os, sys
        sys.path.append(os.path.dirname(cfg.__file__) + '/mdict_query')
        from calibre_plugins.dsreader_helper.mdict_query import mdict_query

        from calibre.srv.library_broker import load_gui_libraries
        library_paths = load_gui_libraries()
        gui_libraries = {os.path.basename(l):l for l in library_paths}
        dic_library_name = c[cfg.KEY_DICT_VIEWER_LIBRARY_NAME]
        if dic_library_name not in gui_libraries:
            return
        
        dic_library_path = gui_libraries[dic_library_name]
        from calibre.db.legacy import LibraryDatabase
        dic_library = LibraryDatabase(dic_library_path, read_only=True, is_second_db=True)
        from calibre.constants import cache_dir
        dic_cache_dir = os.path.join(cache_dir(), 'dsreader_helper_dictionaries')
        for book_id in dic_library.all_ids():
            formats = dic_library.get_field(book_id, 'formats', index_is_id=True)
            print('dic formats %s' % str(formats))
            if 'ZIP' not in formats:
                continue
        
            dicbook_title = dic_library.get_field(book_id, 'title', index_is_id=True)
            dicbook_fmt_path = dic_library.format_abspath(book_id, 'ZIP', index_is_id=True)
            from pathlib import Path
            dicbook_basename = Path(dicbook_fmt_path).stem
            print('unzip %s %s' % (dic_cache_dir, dicbook_basename))
            dicbook_cache_dir = os.path.join(dic_cache_dir, dicbook_basename)
            unzip(dicbook_fmt_path, dicbook_cache_dir)
            mdx_filenames = list(Path(dicbook_cache_dir).rglob("*.[mM][dD][xX]"))
            for mdx_filename in mdx_filenames:
                print('dict builder mdx %s' % mdx_filename)
                self.builders[dicbook_title] = {
                        'basepath': os.path.dirname(mdx_filename),
                        'builder': mdict_query.IndexBuilder(mdx_filename)
                    }
                print('dict builders: %s %s' % (str(self), str(self.builders)))

def unzip(src_path, dst_dir, pwd=None):
    with ZipFile(src_path) as zf:
        members = zf.namelist()
        for member in members:
            arch_info = zf.getinfo(member)
            arch_name = arch_info.filename.replace('/', os.path.sep)
            dst_path = os.path.join(dst_dir, arch_name)
            dst_path = os.path.normpath(dst_path)
            # print('unzip dst_path %s' % dst_path)
            if not os.path.exists(dst_path):
                p = zf.extract(arch_info, dst_dir, pwd)
                # print('unzip %s' % p)
