#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2021, Drearycold <drearycold@gmail.com>'
__docformat__ = 'restructuredtext en'

import six
from six import text_type as unicode
import json, os, copy

try:
    from PyQt5 import QtCore
    from PyQt5 import QtWidgets as QtGui
    from PyQt5.Qt import (Qt, QWidget, QGridLayout, QLabel, QPushButton, QUrl,
                          QGroupBox, QComboBox, QVBoxLayout, QCheckBox,
                          QFormLayout, 
                          QLineEdit, QTabWidget, QAbstractItemView,
                          QTableWidget, QHBoxLayout, QSpinBox, QMessageBox, 
                          QTableView, QAbstractTableModel, QModelIndex)
except ImportError:
    from PyQt4 import QtGui, QtCore
    from PyQt4.Qt import (Qt, QWidget, QGridLayout, QLabel, QPushButton, QUrl,
                          QGroupBox, QComboBox, QVBoxLayout, QCheckBox,
                          QLineEdit, QTabWidget,QAbstractItemView,
                          QTableWidget, QHBoxLayout, QSpinBox)

from calibre.utils.config import JSONConfig
from calibre.srv.opts import server_config

try:
    load_translations()
except NameError:
    pass # load_translations() added in calibre 1.9

PREFS_NAMESPACE = 'DSReaderHelperPlugin'
PREFS_KEY_READING_POSITION_OPTIONS = 'readingPositionOptions'
PREFS_KEY_READING_POSITION_COLUMNS = 'readingPositionColumns'

STORE_NAME = 'Options'

KEY_SERVICE_PORT = 'servicePort'
KEY_GOODREADS_SYNC_ENABLED = 'goodreadsSyncEnabled'
KEY_READING_POSITION_COLUMN_NAME = 'readingPositionColumnName'
KEY_READING_POSITION_COLUMN_PREFIX = 'readingPositionColumnPrefix'
KEY_READING_POSITION_COLUMN_USER_SEPARATED = 'readingPositionColumnUserSeparated'
KEY_READING_POSITION_COLUMN_ALL_LIBRARY = 'readingPositionColumnAllLibrary'
KEY_DICT_VIEWER_ENABLED = 'dictViewerEnabled'
KEY_DICT_VIEWER_LIBRARY_NAME = 'dictViewerLibraryName'
KEY_DICT_VIEWER_ORDERED_LIST = 'dictViewerOrderedList'

PLUGIN_ICONS = [
                'images/dsreader.png',
                ]

KEY_SCHEMA_VERSION = 'SchemaVersion'
DEFAULT_SCHEMA_VERSION = 0.2

DEFAULT_STORE_VALUES = {
                        KEY_SERVICE_PORT: server_config().port + 1,
                        KEY_GOODREADS_SYNC_ENABLED: True,
                        KEY_READING_POSITION_COLUMN_NAME: 'Reading Position',
                        KEY_READING_POSITION_COLUMN_PREFIX: 'read_pos',
                        KEY_READING_POSITION_COLUMN_USER_SEPARATED: True,
                        KEY_READING_POSITION_COLUMN_ALL_LIBRARY: False,
                        KEY_DICT_VIEWER_ENABLED: False,
                        KEY_DICT_VIEWER_LIBRARY_NAME: 'Dictionaries',
                        KEY_DICT_VIEWER_ORDERED_LIST: {},  #library name -> list of dictionaries
                    }

# This is where all preferences for this plugin will be stored
plugin_prefs = JSONConfig('plugins/DSReader Helper')
plugin_prefs.defaults[STORE_NAME] = DEFAULT_STORE_VALUES

dict_builders = {}

def get_library_reading_position_options(db):
    return db.prefs.get_namespaced(PREFS_NAMESPACE, PREFS_KEY_READING_POSITION_OPTIONS, {})

def set_library_reading_position_options(db, options):
    db.prefs.set_namespaced(PREFS_NAMESPACE, PREFS_KEY_READING_POSITION_OPTIONS, options)

def get_library_reading_position_columns(db):
    return db.prefs.get_namespaced(PREFS_NAMESPACE, PREFS_KEY_READING_POSITION_COLUMNS, {})

def set_library_reading_position_columns(db, columns):
    db.prefs.set_namespaced(PREFS_NAMESPACE, PREFS_KEY_READING_POSITION_COLUMNS, columns)

def get_pref(prefs, KEY):
    return prefs.get(
                KEY, plugin_prefs[STORE_NAME].get(
                    KEY,
                    DEFAULT_STORE_VALUES[KEY]
                )
            )

class ConfigWidget(QWidget):

    def __init__(self, plugin_action):
        QWidget.__init__(self)
        self.plugin_action = plugin_action
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        tab_widget = QTabWidget(self)
        layout.addWidget(tab_widget)

        self.service_tab = ServiceTab(self)
        self.dict_viewer_tab = DictViewerTab(self)
        tab_widget.addTab(self.service_tab, _('Service'))
        tab_widget.addTab(self.dict_viewer_tab, _('Dictionary'))

    def save_settings(self):
        new_prefs = {}
        new_prefs[KEY_SERVICE_PORT] = self.service_tab.port_spinbox.value()
        new_prefs[KEY_GOODREADS_SYNC_ENABLED] = self.service_tab.goodreads_sync_enabled_checkbox.isChecked()
        new_prefs[KEY_READING_POSITION_COLUMN_NAME] = self.service_tab.position_column_name_ledit.text()
        new_prefs[KEY_READING_POSITION_COLUMN_PREFIX] = self.service_tab.position_column_prefix_ledit.text()
        new_prefs[KEY_READING_POSITION_COLUMN_USER_SEPARATED] = self.service_tab.position_column_user_separate_checkbox.isChecked()
        new_prefs[KEY_READING_POSITION_COLUMN_ALL_LIBRARY] = self.service_tab.position_column_all_libraries_checkbox.isChecked()

        new_prefs[KEY_DICT_VIEWER_ENABLED] = self.dict_viewer_tab.dictionary_viewer_checkbox.isChecked()
        new_prefs[KEY_DICT_VIEWER_LIBRARY_NAME] = self.dict_viewer_tab.dictionary_viewer_library_combobox.selected_value()
        new_prefs[KEY_DICT_VIEWER_ORDERED_LIST] = self.dict_viewer_tab.library_dict_ordered_list

        plugin_prefs[STORE_NAME] = new_prefs

class ServiceTab(QWidget):

    def __init__(self, parent_dialog):
        self.parent_dialog = parent_dialog
        QWidget.__init__(self)
        layout = QVBoxLayout()
        self.setLayout(layout)

        c = plugin_prefs[STORE_NAME]
        self.db_columns = {}

        library_columns = get_library_reading_position_options(self.parent_dialog.plugin_action.gui.current_db)

        service_group_box = QGroupBox(_('Service options:'), self)
        layout.addWidget(service_group_box)
        service_group_box_layout = QGridLayout()
        service_group_box.setLayout(service_group_box_layout)

        self.port_label = QLabel(_('Service &Port:'), self)
        self.port_label_note = QLabel(_('Please restart calibre to make new settings take effect'), self)
        toolTip = _('Listening port, defaults to content server port number + 1')
        self.port_label.setToolTip(toolTip)
        self.port_spinbox = QSpinBox(self)
        self.port_spinbox.setToolTip(toolTip)
        self.port_label.setBuddy(self.port_spinbox)
        self.port_spinbox.setMinimum(1024)
        self.port_spinbox.setMaximum(65535)
        
        service_group_box_layout.addWidget(self.port_label, 0, 0, 1, 1)
        service_group_box_layout.addWidget(self.port_spinbox, 0, 1, 1, 2)
        service_group_box_layout.addWidget(self.port_label_note, 1, 1, 1, 2)

        self.port_spinbox.setValue(c[KEY_SERVICE_PORT])
        
        self.goodreads_sync_enabled_checkbox = QCheckBox(_('Enable Goodreads Sync'), self)
        self.goodreads_sync_enabled_checkbox.setToolTip(_('Enable automatically updating reading progress to Goodreads account.'))
        self.goodreads_sync_enabled_checkbox.setChecked(c.get(KEY_GOODREADS_SYNC_ENABLED, True))

        service_group_box_layout.addWidget(self.goodreads_sync_enabled_checkbox, 2, 0, 1, 3)

        # ----------
        position_column_box = QGroupBox(_('Reading Position Column options:'), self)
        layout.addWidget(position_column_box)
        position_column_box_layout = QGridLayout()
        position_column_box.setLayout(position_column_box_layout)

        position_column_box_layout.addWidget(QLabel(_('Column Name:'), self), 0, 0, 1, 1)
        self.position_column_name_ledit = QLineEdit(get_pref(library_columns, KEY_READING_POSITION_COLUMN_NAME), self)
        position_column_box_layout.addWidget(self.position_column_name_ledit, 0, 1, 1, 1)
        
        position_column_box_layout.addWidget(QLabel(_('Column Prefix:'), self), 1, 0, 1, 1)

        self.position_column_prefix_ledit = QLineEdit(get_pref(library_columns, KEY_READING_POSITION_COLUMN_PREFIX), self)
        position_column_box_layout.addWidget(self.position_column_prefix_ledit, 1, 1, 1, 1)

        self.position_column_user_separate_checkbox = QCheckBox(_('User-Separated Columns'), self)
        self.position_column_user_separate_checkbox.setChecked(get_pref(library_columns, KEY_READING_POSITION_COLUMN_USER_SEPARATED))
        self.position_column_user_separate_checkbox.setToolTip(_('Add separate Reading Position Column for each user, or a single column for all users'))
        position_column_box_layout.addWidget(self.position_column_user_separate_checkbox, 2, 0, 1, 1)

        self.position_column_all_libraries_checkbox = QCheckBox(_('Apply to All Libraries'), self)
        self.position_column_all_libraries_checkbox.setChecked(get_pref(library_columns, KEY_READING_POSITION_COLUMN_ALL_LIBRARY))
        self.position_column_all_libraries_checkbox.setToolTip(_('Add Reading Position Columns to all libraries lacking them, or only to current library'))
        position_column_box_layout.addWidget(self.position_column_all_libraries_checkbox, 2, 1, 1, 1)

        self.check_reading_position_column_button = QPushButton(_('Name Check'), self)
        self.check_reading_position_column_button.setToolTip(_('Check if there are any conflicting column'))
        self.check_reading_position_column_button.clicked.connect(self.check_position_columns)
        position_column_box_layout.addWidget(self.check_reading_position_column_button, 3, 0, 1, 1)

        self.add_reading_position_column_button = QPushButton(_('Commit Changes'), self)
        self.add_reading_position_column_button.setToolTip(_('Save and Add Reading Position Columns'))
        self.add_reading_position_column_button.clicked.connect(self.add_position_columns)
        position_column_box_layout.addWidget(self.add_reading_position_column_button, 3, 1, 1, 1)

        # -----------
        
    def add_position_columns(self):
        self.generate_position_columns()

        columns_needed = 0
        columns_exist = 0
        columns_added = 0
        columns_error = 0
        from calibre.db.legacy import LibraryDatabase
        for library_name in self.db_columns:
            library_path = self.db_columns[library_name]['library_path']
            library_options = self.db_columns[library_name][PREFS_KEY_READING_POSITION_OPTIONS]
            library_options[KEY_READING_POSITION_COLUMN_NAME] = self.position_column_name_ledit.text()
            library_options[KEY_READING_POSITION_COLUMN_PREFIX] = self.position_column_prefix_ledit.text()
            library_options[KEY_READING_POSITION_COLUMN_USER_SEPARATED] = self.position_column_user_separate_checkbox.isChecked()

            db = LibraryDatabase(library_path, read_only=False, is_second_db=True)

            library_columns = self.db_columns[library_name][PREFS_KEY_READING_POSITION_COLUMNS]
            for user_name in library_columns:
                column_info = library_columns[user_name]
                ret = 0
                exc = ''
                columns_needed += 1
                if not column_info['exists']:
                    try:
                        ret = db.create_custom_column(
                            column_info['label'],
                            column_info['name'],
                            'comments',
                            False,
                            display={
                                'description': column_info['name'],
                                'heading_position': 'hide',
                                'interpret_as': 'long-text'
                            }
                        )
                        columns_added += 1
                        column_info['exists'] = True
                    except BaseException as e:
                        ret = -1
                        exc = str(e)
                        columns_error += 1

                    column_info['ret'] = ret
                    column_info['exc'] = exc
                else:
                    columns_exist += 1

            set_library_reading_position_options(db, library_options)
            set_library_reading_position_columns(db, library_columns)
            db.close()

        msg = 'Libraries: %d\nColumns Needed: %d\nColumns Already Exist: %d\nColumns Added: %d\n' \
                % (len(self.db_columns), columns_needed, columns_exist, columns_added)
        if columns_error > 0:
            msg += 'Failed: %d' % columns_error
        else:
            msg += 'All Columns Ready'
        msgbox = QMessageBox(self.parent_dialog)
        msgbox.setText(msg)
        return msgbox.exec_()

    def check_position_columns(self):
        self.generate_position_columns()
        
        total = 0
        exist = 0
        for library_name in self.db_columns:
            for user_name in self.db_columns[library_name][PREFS_KEY_READING_POSITION_COLUMNS]:
                total += 1
                exist += self.db_columns[library_name][PREFS_KEY_READING_POSITION_COLUMNS][user_name]['exists']

        msgbox = QMessageBox(self.parent_dialog)
        msgbox.setText('Libraries: %d\nColumns Missing: %d' % (len(self.db_columns), total - exist))
        return msgbox.exec_()

    def generate_position_columns(self):
        label_prefix = self.position_column_prefix_ledit.text()
        desc_name = self.position_column_name_ledit.text()
        self.db_columns = {}

        library_paths = {}
        if self.position_column_all_libraries_checkbox.isChecked():
            from calibre.gui2 import gui_prefs
            library_paths = gui_prefs()['library_usage_stats']
        else:
            library_paths[self.parent_dialog.plugin_action.gui.current_db.library_path] = ''
            
        for library_path in library_paths:
            self.db_columns[os.path.basename(library_path)] = {
                'library_path': library_path,
                PREFS_KEY_READING_POSITION_OPTIONS: {},
                PREFS_KEY_READING_POSITION_COLUMNS: {}
            }

        if self.position_column_user_separate_checkbox.isChecked():
            from calibre.srv.users import UserManager
            userManager = UserManager()
            for username in userManager.all_user_names:
                allowed = userManager.allowed_library_names(
                    username,
                    self.db_columns.keys()
                )
                for library_name in allowed:
                    self.db_columns[library_name][PREFS_KEY_READING_POSITION_COLUMNS][username] = {
                        'label': "%s_%s" % (label_prefix, username),
                        'name': "%s's %s" % (username, desc_name)
                    }
        else:
            for library_name in self.db_columns:
                self.db_columns[library_name][PREFS_KEY_READING_POSITION_COLUMNS]['*'] = {
                    'label': label_prefix,
                    'name': desc_name
                }

        from calibre.db.legacy import LibraryDatabase
        for library_name in self.db_columns:
            library_path = self.db_columns[library_name]['library_path']
            db = LibraryDatabase(library_path, read_only=True, is_second_db=True)
            self.db_columns[library_name][PREFS_KEY_READING_POSITION_OPTIONS] = get_library_reading_position_options(db)

            for user_name in self.db_columns[library_name][PREFS_KEY_READING_POSITION_COLUMNS]:
                column_label = self.db_columns[library_name][PREFS_KEY_READING_POSITION_COLUMNS][user_name]['label']
                self.db_columns[library_name][PREFS_KEY_READING_POSITION_COLUMNS][user_name]['exists'] = column_label in db.custom_column_label_map

class DictViewerTab(QWidget):
    def __init__(self, parent_dialog):
        self.parent_dialog = parent_dialog
        QWidget.__init__(self)
        layout = QVBoxLayout()
        self.setLayout(layout)

        c = plugin_prefs[STORE_NAME]
        self.library_dict_ordered_list = c.get(KEY_DICT_VIEWER_ORDERED_LIST, {})

        print('DictViewerTab builders %s' % str(dict_builders))

        dictionary_column_box = QGroupBox(_(''), self)
        layout.addWidget(dictionary_column_box)
        dictionary_column_box_layout = QGridLayout()
        dictionary_column_box.setLayout(dictionary_column_box_layout)

        self.dictionary_viewer_checkbox = QCheckBox(_('Enable Dictionary Viewer'), self)
        self.dictionary_viewer_checkbox.setChecked(c.get(KEY_DICT_VIEWER_ENABLED, DEFAULT_STORE_VALUES[KEY_DICT_VIEWER_ENABLED]))
        self.dictionary_viewer_checkbox.setToolTip(_('Provide Dictionary for DSReader App'))
        dictionary_column_box_layout.addWidget(self.dictionary_viewer_checkbox, 0, 0, 1, 1)

        from calibre_plugins.dsreader_helper.common_utils import ListComboBox
        from calibre.srv.library_broker import load_gui_libraries
        library_paths = load_gui_libraries()
        gui_libraries = {os.path.basename(l):l for l in library_paths}
        self.dictionary_viewer_library_combobox = ListComboBox(self, gui_libraries, c.get(KEY_DICT_VIEWER_LIBRARY_NAME, DEFAULT_STORE_VALUES[KEY_DICT_VIEWER_LIBRARY_NAME]))
        self.dictionary_viewer_library_combobox.setToolTip(_('select the library to be used by dictionary viewer'))
        dictionary_column_box_layout.addWidget(QLabel(_('Library Name:'), self), 1, 0, 1, 1)
        dictionary_column_box_layout.addWidget(self.dictionary_viewer_library_combobox, 1, 1, 1, 1)

        self.dictionary_viewer_library_refresh = QPushButton(_('Refresh'), self)
        self.dictionary_viewer_library_refresh.setToolTip(_('refresh recognizable dictionary list'))
        self.dictionary_viewer_library_refresh.clicked.connect(self.refresh_dictionary_list)
        dictionary_column_box_layout.addWidget(self.dictionary_viewer_library_refresh, 1, 2, 1, 1)

        table_hbox = QGroupBox(_('Dictionary List'), self)
        table_hbox_layout = QHBoxLayout()
        table_hbox.setLayout(table_hbox_layout)
        layout.addWidget(table_hbox)
        
        self.dict_table_model = DictViewerTableModel(dict_builders)
        self.dict_table_view = QTableView()
        self.dict_table_view.setModel(self.dict_table_model)
        self.dict_table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.dict_table_view.selectionModel().selectionChanged.connect(self.dict_table_selection_changed)
        table_hbox_layout.addWidget(self.dict_table_view)

        dic_button_vbox = QGroupBox(_(''), self)
        dic_button_vbox_layout = QVBoxLayout()
        dic_button_vbox.setLayout(dic_button_vbox_layout)
        table_hbox_layout.addWidget(dic_button_vbox)

        self.dict_order_up_button = DictOrderButton(_('🔼'), self)
        self.dict_order_up_button.setToolTip(_('Move Up'))
        self.dict_order_up_button.clicked.connect(self.dict_table_order_move_up)
        dic_button_vbox_layout.addWidget(self.dict_order_up_button)

        self.dict_order_import_button = DictOrderButton(_('+'), self)
        self.dict_order_import_button.setToolTip(_('Import'))
        #self.dict_order_import_button.clicked.connect(self.add_position_columns)
        dic_button_vbox_layout.addWidget(self.dict_order_import_button)

        self.dict_order_remove_button = DictOrderButton(_('−'), self)
        self.dict_order_remove_button.setToolTip(_('Remove'))
        #self.dict_order_remove_button.clicked.connect(self.add_position_columns)
        dic_button_vbox_layout.addWidget(self.dict_order_remove_button)

        self.dict_order_down_button = DictOrderButton(_('🔽'), self)
        self.dict_order_down_button.setToolTip(_('Move Down'))
        self.dict_order_down_button.clicked.connect(self.dict_table_order_move_down)
        dic_button_vbox_layout.addWidget(self.dict_order_down_button)

        dict_info_form = QGroupBox(_('Details'), self)
        dict_info_form_layout = QFormLayout()
        dict_info_form.setLayout(dict_info_form_layout)
        layout.addWidget(dict_info_form)

        self.dict_info_form_name = QLabel(_(''), self)
        dict_info_form_layout.addRow(_('Name:'), self.dict_info_form_name)

        self.refresh_dictionary_list()

    def refresh_dictionary_list(self):
        print('refresh_dictionary_list')
        
        dic_library_name = self.dictionary_viewer_library_combobox.selected_value()
        dict_ordered_list = rebuild_dict_builders(dic_library_name)
        self.library_dict_ordered_list[dic_library_name] = dict_ordered_list

        self.dict_table_model = DictViewerTableModel(dict_ordered_list)
        self.dict_table_view.setModel(self.dict_table_model)

    def dict_table_selection_changed(self, selected, deselected):
        print('dict_table_selection_changed %s %s' % (str(selected), str(deselected)))
        for index in self.dict_table_view.selectedIndexes():
            #print('dict_table_selection_changed first %d %d %d %d' % (index.top(), index.left(), index.right(), index.bottom()))
            print('dict_table_selection_changed selected %d %d' % (index.row(), index.column()))

    def dict_table_order_move_up(self):
        selected_indexes = self.dict_table_view.selectedIndexes()
        dict_library_name = self.dictionary_viewer_library_combobox.selected_value()
        dict_ordered_list = self.library_dict_ordered_list.get(dict_library_name, [])
        for index in selected_indexes:
            row = index.row()
            if row > 0:
                dict_ordered_list[row], dict_ordered_list[row-1] = dict_ordered_list[row-1], dict_ordered_list[row]
                self.library_dict_ordered_list[dict_library_name] = dict_ordered_list
                self.dict_table_model = DictViewerTableModel(dict_ordered_list)
                self.dict_table_view.setModel(self.dict_table_model)

    def dict_table_order_move_down(self):
        selected_indexes = self.dict_table_view.selectedIndexes()
        dict_library_name = self.dictionary_viewer_library_combobox.selected_value()
        dict_ordered_list = self.library_dict_ordered_list.get(dict_library_name, [])
        for index in selected_indexes:
            row = index.row()
            if row+1 < len(dict_ordered_list):
                dict_ordered_list[row], dict_ordered_list[row+1] = dict_ordered_list[row+1], dict_ordered_list[row]
                self.library_dict_ordered_list[dict_library_name] = dict_ordered_list
                self.dict_table_model = DictViewerTableModel(dict_ordered_list)
                self.dict_table_view.setModel(self.dict_table_model)

class DictOrderButton(QPushButton):
    def minimumSizeHint(self):
        a = QPushButton.minimumSizeHint(self)
        a.setHeight(40)
        a.setWidth(40)
        return a

class DictViewerTableModel(QAbstractTableModel):
    def __init__(self, dict_ordered_list={}):
        QAbstractTableModel.__init__(self)
        self.dict_ordered_list = dict_ordered_list
        print('DictViewerTableModel %s' % str(self.dict_ordered_list))

    def rowCount(self, parent=QModelIndex()):
        return len(self.dict_ordered_list)
    
    def columnCount(self, parent=QModelIndex()):
        return 3
    
    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return None
        return None

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        column = index.column()
        
        if role == Qt.DisplayRole:
            dict_entry = self.dict_ordered_list[row]
            if column == 0:
                return '#%d' % dict_entry['id']
            if column == 1:
                return dict_entry['title']
            if column == 2:
                return dict_entry['mdx']

def unzip(src_path, dst_dir, pwd=None):
    import zipfile
    with zipfile.ZipFile(src_path) as zf:
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

def rebuild_dict_builders(dict_library_name=None):
    c = plugin_prefs[STORE_NAME]
    dict_builders.clear()
    if not dict_library_name:
        dict_library_name = c.get(KEY_DICT_VIEWER_LIBRARY_NAME, '')

    from calibre.srv.library_broker import load_gui_libraries
    library_paths = load_gui_libraries()
    import os
    gui_libraries = {os.path.basename(l):l for l in library_paths}
    if dict_library_name not in gui_libraries:
        return []

    dic_library_path = gui_libraries[dict_library_name]
    from calibre.db.legacy import LibraryDatabase
    dic_library = LibraryDatabase(dic_library_path, read_only=True, is_second_db=True)
    dic_library_all_ids = dic_library.all_ids()

    # remove non existing ids
    dict_ordered_list = c.get(KEY_DICT_VIEWER_ORDERED_LIST, {}).get(dict_library_name, [])
    dict_ordered_list = [d for d in dict_ordered_list if d.get('id', 0) in dic_library_all_ids]
    for dict_entry in dict_ordered_list:
        dict_entry['title'] = dic_library.get_field(dict_entry['id'], 'title', index_is_id=True)

    # 
    import fnmatch
    import zipfile
    for book_id in dic_library_all_ids:
        formats = dic_library.get_field(book_id, 'formats', index_is_id=True)
        print('dic formats %s' % str(formats))
        if 'ZIP' not in formats:
            continue
    
        dicbook_title = dic_library.get_field(book_id, 'title', index_is_id=True)
        dicbook_fmt_path = dic_library.format_abspath(book_id, 'ZIP', index_is_id=True)
        
        with zipfile.ZipFile(dicbook_fmt_path) as zf:
            members = zf.namelist()
            mdx_files = fnmatch.filter(members, '*.[mM][dD][xX]')
            for mdx_file in mdx_files:
                print('refresh_dictionary_list title %s %s' % (dicbook_title, mdx_file))
                dict_entry = {'id': book_id, 'mdx': mdx_file, 'title': dicbook_title}
                if dict_entry not in dict_ordered_list:
                    dict_ordered_list.append(dict_entry)

    print('refresh_dictionary_list result %s' % str(dict_ordered_list))

    from calibre.constants import cache_dir
    dic_cache_dir = os.path.join(cache_dir(), 'dsreader_helper_dictionaries')
    import os, sys
    sys.path.append(os.path.dirname(__file__) + '/mdict_query')
    from calibre_plugins.dsreader_helper.mdict_query import mdict_query

    for dict_entry in dict_ordered_list:
        dicbook_title = dic_library.get_field(dict_entry['id'], 'title', index_is_id=True)
        dicbook_fmt_path = dic_library.format_abspath(dict_entry['id'], 'ZIP', index_is_id=True)
        from pathlib import Path
        dicbook_basename = Path(dicbook_fmt_path).stem
        print('unzip %s %s' % (dic_cache_dir, dicbook_basename))
        dicbook_cache_dir = os.path.join(dic_cache_dir, dicbook_basename)
        unzip(dicbook_fmt_path, dicbook_cache_dir)
        mdx_filenames = list(Path(dicbook_cache_dir).rglob(dict_entry['mdx']))
        for mdx_filename in mdx_filenames:
            print('dict builder mdx %s' % mdx_filename)
            builder = mdict_query.IndexBuilder(mdx_filename)
            if builder:
                print('builder title: %s' % builder._title)
                dict_builders['%d#%s' % (dict_entry['id'], dict_entry['mdx'])] = {
                        'id': dict_entry['id'],
                        'title': dicbook_title,
                        'basepath': os.path.dirname(mdx_filename),
                        'basename': os.path.basename(mdx_filename), 
                        'builder': builder
                    }
    
    print('rebuild_dict_builders finish %s' % str(dict_builders))

    return dict_ordered_list