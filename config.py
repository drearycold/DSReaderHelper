#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2021, Drearycold <drearycold@gmail.com>'
__docformat__ = 'restructuredtext en'

import six
from six import text_type as unicode

try:
    from PyQt5 import QtCore
    from PyQt5 import QtWidgets as QtGui
    from PyQt5.Qt import (Qt, QWidget, QGridLayout, QLabel, QPushButton, QUrl,
                          QGroupBox, QComboBox, QVBoxLayout, QCheckBox,
                          QLineEdit, QTabWidget, QAbstractItemView,
                          QTableWidget, QHBoxLayout, QSpinBox)
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
PREFS_KEY_SETTINGS = 'settings'

STORE_NAME = 'Options'

KEY_SERVICE_PORT = 'servicePort'
KEY_GOODREADS_SYNC_ENABLED = 'goodreadsSyncEnabled'


PLUGIN_ICONS = [
                'images/dsreader.png',
                ]

KEY_SCHEMA_VERSION = 'SchemaVersion'
DEFAULT_SCHEMA_VERSION = 0.1

DEFAULT_STORE_VALUES = {
                        KEY_SERVICE_PORT: server_config().port + 1,
                        KEY_GOODREADS_SYNC_ENABLED: True,
                        }

# This is where all preferences for this plugin will be stored
plugin_prefs = JSONConfig('plugins/DSReader Helper')
plugin_prefs.defaults[STORE_NAME] = DEFAULT_STORE_VALUES


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

        plugin_prefs[STORE_NAME] = new_prefs

class ServiceTab(QWidget):

    def __init__(self, parent_dialog):
        self.parent_dialog = parent_dialog
        QWidget.__init__(self)
        layout = QVBoxLayout()
        self.setLayout(layout)

        c = plugin_prefs[STORE_NAME]
        
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

        position_column_box_layout.addWidget(QLabel(_('Column Prefix:'), self), 0, 0, 1, 1)
        self.position_column_prefix_ledit = QLineEdit('read_pos', self)
        position_column_box_layout.addWidget(self.position_column_prefix_ledit, 0, 1, 1, 1)

        self.position_column_all_libraries_checkbox = QCheckBox(_('All Libraries'), self)
        self.position_column_all_libraries_checkbox.setChecked(True)
        self.position_column_all_libraries_checkbox.setToolTip(_('Add Reading Position Columns to all libraries lacking them'))
        position_column_box_layout.addWidget(self.position_column_all_libraries_checkbox, 0, 2, 1, 1)

        self.add_reading_position_column_button = QPushButton(_('Add'), self)
        self.add_reading_position_column_button.setToolTip(_('Add Reading Position Columns'))
        self.add_reading_position_column_button.clicked.connect(self.add_position_columns)
        position_column_box_layout.addWidget(self.add_reading_position_column_button, 0, 3, 1, 1)

    def add_position_columns(self):
        print("add_position_columns %s %s" % (self.position_column_all_libraries_checkbox.isChecked(), self.position_column_prefix_ledit.text()))
        pass