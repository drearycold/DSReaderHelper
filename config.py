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
                          QLineEdit, QTabWidget, QAbstractItemView,
                          QTableWidget, QHBoxLayout, QSpinBox, QMessageBox)
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
                        KEY_DICT_VIEWER_ENABLED: True,
                        KEY_DICT_VIEWER_LIBRARY_NAME: 'Dictionaries'
                    }

# This is where all preferences for this plugin will be stored
plugin_prefs = JSONConfig('plugins/DSReader Helper')
plugin_prefs.defaults[STORE_NAME] = DEFAULT_STORE_VALUES

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
        tab_widget.addTab(self.service_tab, _('Service'))

    def save_settings(self):
        new_prefs = {}
        new_prefs[KEY_SERVICE_PORT] = self.service_tab.port_spinbox.value()
        new_prefs[KEY_GOODREADS_SYNC_ENABLED] = self.service_tab.goodreads_sync_enabled_checkbox.isChecked()
        new_prefs[KEY_READING_POSITION_COLUMN_NAME] = self.service_tab.position_column_name_ledit.text()
        new_prefs[KEY_READING_POSITION_COLUMN_PREFIX] = self.service_tab.position_column_prefix_ledit.text()
        new_prefs[KEY_READING_POSITION_COLUMN_USER_SEPARATED] = self.service_tab.position_column_user_separate_checkbox.isChecked()
        new_prefs[KEY_READING_POSITION_COLUMN_ALL_LIBRARY] = self.service_tab.position_column_all_libraries_checkbox.isChecked()

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

        self.check_reading_position_column_button = QPushButton(_('Healthy Check'), self)
        self.check_reading_position_column_button.setToolTip(_('Check if there are any conflicting column'))
        self.check_reading_position_column_button.clicked.connect(self.check_position_columns)
        position_column_box_layout.addWidget(self.check_reading_position_column_button, 3, 0, 1, 1)

        self.add_reading_position_column_button = QPushButton(_('Commit Changes'), self)
        self.add_reading_position_column_button.setToolTip(_('Save and Add Reading Position Columns'))
        self.add_reading_position_column_button.clicked.connect(self.add_position_columns)
        position_column_box_layout.addWidget(self.add_reading_position_column_button, 3, 1, 1, 1)

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
