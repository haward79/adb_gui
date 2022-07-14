
"""
    TODO
    adb push/pull check path exist and do for file and directory(recursive)
"""

import os
import subprocess
import sys
from datetime import datetime
from PyQt6.QtCore import Qt, QCoreApplication, QUrl
from PyQt6.QtGui import QImage, QPixmap, QIcon, QAction, QDesktopServices
from PyQt6.QtWidgets import QSizePolicy, QSpacerItem, QApplication, QMainWindow, QScrollArea, QWidget, QMenuBar, QLabel, QPushButton, QGridLayout, QVBoxLayout, QHBoxLayout
from filesystem import *
from adb import is_server_startup, device_list, Adb
from log import *


DEFAULT_REMOTE_PATH = '/storage/self/primary/'
PREVIEW_PATH = os.getcwd() + '/preview'
IMAGE_EXTENSION_NAME = ('.jpg', '.png', '.ico', '.svg')


if not DEFAULT_REMOTE_PATH.endswith('/'):
    DEFAULT_REMOTE_PATH += '/'


def load_image(filename: str) -> QPixmap:

    q_pixmap = None

    try:
        q_image = QImage(filename)
        q_image = q_image.scaledToHeight(80, Qt.TransformationMode.SmoothTransformation)

        q_pixmap = QPixmap.fromImage(q_image)

    except Exception as e:
        log('Failed to load image: ' + filename, LogType.ERROR)

        return None

    return q_pixmap


def generate_item(index: int, icon_filename: str, name: str, is_dir: bool, descript: str, callback, parent) -> None:

    icon = QLabel()
    filename = QLabel()
    description = QLabel()
    access = QPushButton()

    icon.setPixmap(load_image(icon_filename))
    filename.setStyleSheet('letter-spacing:0.5px;')
    description.setStyleSheet('color:#7A7A7A; letter-spacing:0.5px;')
    access.setFixedWidth(30)
    access.setFixedHeight(30)

    filename.setText(name)
    description.setText(descript)

    if is_dir:
        access.setText('>')
        access.clicked.connect(callback)
        access.setProperty('type', 'directory')
        access.setProperty('dir_name', name)
        parent.addWidget(access, index, 2, 2, 1, Qt.AlignmentFlag.AlignRight and Qt.AlignmentFlag.AlignHCenter)
    else:
        access.setText('=')
        access.clicked.connect(callback)
        access.setProperty('type', 'file')
        access.setProperty('filename', name)
        parent.addWidget(access, index, 2, 2, 1, Qt.AlignmentFlag.AlignRight and Qt.AlignmentFlag.AlignHCenter)

    parent.addWidget(icon, index, 0, 2, 1, Qt.AlignmentFlag.AlignLeft and Qt.AlignmentFlag.AlignHCenter)
    parent.addWidget(filename, index, 1, 1, 1, Qt.AlignmentFlag.AlignLeft and Qt.AlignmentFlag.AlignBottom)
    parent.addWidget(description, index + 1, 1, 1, 1, Qt.AlignmentFlag.AlignLeft and Qt.AlignmentFlag.AlignTop)


class AdbGui(QMainWindow):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.devices = []
        self.device_items = []
        self.device_id = ''
        self.device_path = ''
        self.adbc = Adb()
        self.local_path = os.path.expanduser('~')

        if not self.local_path.endswith('/'):
            self.local_path += '/'

        if os.path.isdir(self.local_path + 'Desktop'):
            self.local_path += 'Desktop/'

        self.menubar = QMenuBar()
        self.menuItem_operation = self.menubar.addMenu('Operation')
        self.menuItem_devices = self.menubar.addMenu('Device')
        self.menuItem_help = self.menubar.addMenu('Help')

        self.menuItem_operation.addAction('Reload device list', self.load_devices)
        self.menuItem_operation.addAction('Reload device file explorer', self.load_remote)
        self.menuItem_operation.addAction('Reload local file explorer', self.load_local)

        self.menuItem_help.addAction('Get online document', self.visit_website)
        self.menuItem_help.addAction('About', self.show_about)

        self.label_remoteLocation = QLabel('Remote: ')
        self.label_remoteLocation.setAlignment(Qt.AlignmentFlag.AlignBottom)

        self.label_localLocation = QLabel('Local: ')
        self.label_localLocation.setAlignment(Qt.AlignmentFlag.AlignBottom)

        self.hlayout_locationSection = QHBoxLayout()
        self.hlayout_locationSection.setContentsMargins(10, 10, 10, 0)
        self.hlayout_locationSection.setSpacing(0)
        self.hlayout_locationSection.addWidget(self.label_remoteLocation)
        self.hlayout_locationSection.addWidget(self.label_localLocation)

        self.scrollArea_remote = QScrollArea()
        self.scrollArea_remote.setWidgetResizable(True)

        self.scrollArea_local = QScrollArea()
        self.scrollArea_local.setWidgetResizable(True)

        self.hlayout_fileSection = QHBoxLayout()
        self.hlayout_fileSection.addWidget(self.scrollArea_remote)
        self.hlayout_fileSection.addWidget(self.scrollArea_local)

        self.widget_locationSection = QWidget()
        self.widget_locationSection.setLayout(self.hlayout_locationSection)

        self.widget_fileSection = QWidget()
        self.widget_fileSection.setLayout(self.hlayout_fileSection)

        self.vbox_layout = QVBoxLayout()
        self.vbox_layout.setContentsMargins(0, 0, 0, 0)
        self.vbox_layout.setSpacing(0)
        self.vbox_layout.addWidget(self.menubar)
        self.vbox_layout.addWidget(self.widget_locationSection)
        self.vbox_layout.addWidget(self.widget_fileSection)

        self.widget_mainSection = QWidget()
        self.widget_mainSection.setLayout(self.vbox_layout)

        self.setCentralWidget(self.widget_mainSection)
        self.setMinimumWidth(900)
        self.setMinimumHeight(500)
        self.setWindowTitle("Adb GUI")
        self.setWindowIcon(QIcon('images/icon.png'))

        if not is_server_startup():
            show_message(
                'Adb server is NOT startup. Please start it manually.\nYou can run \"adb start-server\" in terminal to start it.',
                'Adb server not startup',
                LogType.ERROR
            )

            QCoreApplication.exit()

        self.load_devices()
        self.load_local()


    def load_devices(self) -> None:

        # Clear item from device menu.
        for item in self.device_items:
            item.setVisible(False)

        # Clear devices and menu items.
        self.devices = []
        self.device_items = []

        # Get device list from adb server.
        self.devices = device_list()

        # Update device list and device menu.
        if len(self.devices) > 0:
            for device in self.devices:
                item = QAction(device, self.menuItem_devices)
                item.triggered.connect(self.select_device)
                self.menuItem_devices.addAction(item)
                self.device_items.append(item)

        else:
            item = QAction('No device')
            item.setEnabled(False)
            self.menuItem_devices.addAction(item)
            self.device_items.append(item)

        # Clear current device id and device path.
        self.device_id = ''
        self.device_path = ''

        # Reload remote file explorer.
        self.load_remote()


    def select_device(self):

        device_id = self.sender().text()

        if self.adbc.connect(device_id):
            self.device_id = device_id
            self.device_path = '/'

            if self.adbc.is_path_exists(DEFAULT_REMOTE_PATH):
                self.device_path = DEFAULT_REMOTE_PATH

            for item in self.device_items:
                if item.text() == self.device_id:
                    item.setIcon(QIcon('images/checked.png'))
                else:
                    item.setIcon(QIcon())

            self.load_remote()

        else:
            show_message(
                'Failed to connect to device: ' + device_id + '.\nPlease reload device list or reconnect device by adb command.',
                'Failed to connect to device',
                LogType.ERROR
            )


    def load_remote(self):

        if len(self.device_id) == 0:
            self.label_remoteLocation.setText('Remote: ' + self.device_path)
        else:
            self.label_remoteLocation.setText('Connected to ' + self.device_id + '\n\nRemote: ' + self.device_path)

        gridLayout_remoteSection = QGridLayout()
        widget_remoteSection = QWidget()

        gridLayout_remoteSection.setSpacing(10)
        gridLayout_remoteSection.setColumnStretch(0, 1)
        gridLayout_remoteSection.setColumnStretch(1, 10)
        gridLayout_remoteSection.setColumnStretch(2, 1)

        if len(self.device_id) == 0 or len(self.device_path) == 0:
            pass

        else:
            index = 0
            content = self.adbc.get_directory_struct(self.device_path).get_content()

            generate_item(index, 'images/back.png', '..', True, 'Back to parent directory', self.access_remote_directory, gridLayout_remoteSection)
            index += 2

            for c in content:
                if type(c) is File:
                    icon_path = 'images/file.png'

                    for extname in IMAGE_EXTENSION_NAME:
                        if c.get_fullname().lower().endswith(extname.lower()):
                            if self.adbc.pull(c.get_path_fullname(), PREVIEW_PATH):
                                icon_path = PREVIEW_PATH
                            else:
                                log('Failed to pull file for preview: ' + c.get_path_fullname(), LogType.ERROR)

                            break

                    descript = 'File | ' + readable_size(c.get_size()) + ' | ' + c.get_datetime()
                    generate_item(index, icon_path, c.get_fullname(), False, descript, self.access_remote_directory, gridLayout_remoteSection)

                    if icon_path == PREVIEW_PATH:
                        os.remove(PREVIEW_PATH)
                else:
                    items_count = len(self.adbc.get_directory_struct(c.get_path_dirname()).get_content())
                    descript = 'Directory | ' + str(items_count) + ' items | ' + c.get_datetime()
                    generate_item(index, 'images/directory.png', c.get_basename(), True, descript, self.access_remote_directory, gridLayout_remoteSection)

                index += 2

            gridLayout_remoteSection.addItem(QSpacerItem(10, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding), index, 0, 1, 3)

        widget_remoteSection.setLayout(gridLayout_remoteSection)
        self.scrollArea_remote.setWidget(widget_remoteSection)


    def load_local(self):

        self.label_localLocation.setText('Local: ' + self.local_path)

        gridLayout_localSection = QGridLayout()
        widget_localSection = QWidget()

        gridLayout_localSection.setSpacing(10)
        gridLayout_localSection.setColumnStretch(0, 1)
        gridLayout_localSection.setColumnStretch(1, 10)
        gridLayout_localSection.setColumnStretch(2, 1)

        index = 0
        content = os.listdir(self.local_path)

        generate_item(index, 'images/back.png', '..', True, 'Back to parent directory', self.access_local_directory, gridLayout_localSection)
        index += 2

        for c in content:
            path_filename = self.local_path + c

            if os.path.isfile(path_filename):
                icon_path = 'images/file.png'

                for extname in IMAGE_EXTENSION_NAME:
                    if c.lower().endswith(extname.lower()):
                        cmd = 'cp' + ' \'' + path_filename + '\'' + ' \'' + PREVIEW_PATH + '\''
                        process = subprocess.Popen(args=cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        stdout, stderr = process.communicate()

                        stdout = stdout.decode('utf-8')
                        stderr = stderr.decode('utf-8')

                        if len(stderr) == 0:
                            icon_path = PREVIEW_PATH
                        else:
                            log('Failed to copy file for preview: ' + c.get_path_fullname(), LogType.ERROR)

                        break

                file_size = readable_size(os.path.getsize(path_filename))
                file_modified = datetime.fromtimestamp(os.path.getmtime(path_filename)).strftime('%Y.%m.%d %H:%M:%S')
                descript = 'File | ' + file_size + ' | ' + file_modified
                generate_item(index, icon_path, c, False, descript, self.access_local_directory, gridLayout_localSection)

                if icon_path == PREVIEW_PATH:
                    os.remove(PREVIEW_PATH)

            elif os.path.isdir(path_filename):
                items_count = len(os.listdir(path_filename))
                file_modified = datetime.fromtimestamp(os.path.getmtime(path_filename)).strftime('%Y.%m.%d %H:%M:%S')
                descript = 'Directory | ' + str(items_count) + ' items | ' + file_modified
                generate_item(index, 'images/directory.png', c, True, descript, self.access_local_directory, gridLayout_localSection)

            index += 2

        gridLayout_localSection.addItem(QSpacerItem(10, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding), index, 0, 1, 3)

        widget_localSection.setLayout(gridLayout_localSection)
        self.scrollArea_local.setWidget(widget_localSection)


    def access_remote_directory(self):

        event_sender_type = self.sender().property('type')

        if event_sender_type == 'directory':
            dir_name = self.sender().property('dir_name')

            if dir_name == '..':
                if self.device_path != '/':
                    self.device_path = self.device_path[0:-1]
                    pos = self.device_path.rfind('/')
                    self.device_path = self.device_path[0:pos + 1]
            else:
                self.device_path += dir_name + '/'

            self.load_remote()

        else:
            filename = self.sender().property('filename')

            if self.adbc.pull(self.device_path + filename, self.local_path + filename):
                self.load_local()
            else:
                self.load_remote()

                log_msg = 'Failed to pull file from device "' + (self.device_path + filename) + '" to local "' + (self.local_path + filename) + '"'

                log(log_msg, LogType.ERROR)

                show_message(
                    log_msg,
                    'Failed to pull from device',
                    LogType.ERROR
                )


    def access_local_directory(self):

        event_sender_type = self.sender().property('type')

        if event_sender_type == 'directory':
            dir_name = self.sender().property('dir_name')

            if dir_name == '..':
                if self.local_path != '/':
                    self.local_path = self.local_path[0:-1]
                    pos = self.local_path.rfind('/')
                    self.local_path = self.local_path[0:pos+1]
            else:
                self.local_path += dir_name + '/'

            self.load_local()

        else:
            filename = self.sender().property('filename')

            if self.adbc.push(self.local_path + filename, self.device_path + filename):
                self.load_remote()
            else:
                self.load_local()

                log_msg = 'Failed to push file from local, "' + (self.local_path + filename) + '" to device, "' + (self.device_path + filename) + '"'

                log(log_msg, LogType.ERROR)

                show_message(
                    log_msg,
                    'Failed to push to device',
                    LogType.ERROR
                )


    def visit_website(self):

        QDesktopServices.openUrl(QUrl('https://github.com/haward79/adb_gui'))


    def show_about(self):

        show_message(
            'Adb GUI is a GUI wrapper for adb.\n\nCurrent version is v1.0.0',
            'About this program',
            LogType.INFO
        )


app = QApplication(sys.argv)
window = AdbGui()

window.show()

sys.exit(app.exec())
