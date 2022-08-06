
"""
    TODO
    adb push/pull check path exist and do for file and directory(recursive)
"""

pos = __file__.rfind('/')

if pos != -1:
    RESOURCE_PATH = __file__[:pos] + '/'
else:
    RESOURCE_PATH = ''

print(RESOURCE_PATH)


import os
import subprocess
import sys
import cv2
from datetime import datetime
from time import sleep
from PyQt6.QtCore import Qt, QCoreApplication, QObject, QThread, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap, QIcon, QAction, QDesktopServices
from PyQt6.QtWidgets import QSizePolicy, QSpacerItem, QApplication, QMainWindow, QStatusBar, QScrollArea, QWidget, QMenuBar, QLabel, QPushButton, QGridLayout, QVBoxLayout, QHBoxLayout
from filesystem import *
from adb import is_server_startup, device_list, Adb
from log import *


STATUSBAR_MESSAGE_TIMEOUT_MS = 3000
DEFAULT_REMOTE_PATH = '/storage/self/primary/'
PREVIEW_PATH = os.getcwd() + '/preview'
IMAGE_EXTENSION_NAME = ('.jpg', '.jpeg', '.png', '.ico', '.svg')
VIDEO_EXTENSION_NAME = ('.mp4', '.avi', '.webm')
IMAGE_MAX_HEIGHT = 80
IMAGE_MAX_WIDTH = 150


if not DEFAULT_REMOTE_PATH.endswith('/'):
    DEFAULT_REMOTE_PATH += '/'


def create_video_thumbnail(icon_filename: str, original_filename: str = None) -> QPixmap:

    if original_filename is None:
        original_filename = icon_filename

    cap = cv2.VideoCapture(icon_filename)
    frame_id = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) // 2
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)

    status, frame = cap.read()

    if status:
        frame = cv2.resize(frame, (int(frame.shape[1] * (IMAGE_MAX_HEIGHT / frame.shape[0])), IMAGE_MAX_HEIGHT))

        if frame.shape[1] > IMAGE_MAX_WIDTH:
            left_boundary = (frame.shape[1] - IMAGE_MAX_WIDTH) // 2
            frame = frame[:, left_boundary:left_boundary+IMAGE_MAX_WIDTH]

        h, w, c = frame.shape

        return QPixmap(QImage(frame, w, h, 3 * w, QImage.Format.Format_RGB888))
    else:
        log('Failed to create thumbnail for video: ' + original_filename, LogType.ERROR)

        return None


def create_image_thumbnail(icon_filename: str, original_filename: str = None) -> QPixmap:

    if original_filename is None:
        original_filename = icon_filename

    try:
        q_image = QImage(icon_filename)
        q_image = q_image.scaledToHeight(IMAGE_MAX_HEIGHT, Qt.TransformationMode.SmoothTransformation)

        if q_image.width() > IMAGE_MAX_WIDTH:
            q_image = q_image.copy((q_image.width()-IMAGE_MAX_WIDTH)//2, 0, IMAGE_MAX_WIDTH, q_image.height())

        return QPixmap.fromImage(q_image)

    except Exception as e:
        log('Failed to create thumbnail for image: ' + original_filename, LogType.ERROR)

        return None


def remove_thumbnail():

    if os.path.isfile(PREVIEW_PATH):
        os.remove(PREVIEW_PATH)


def local_copy(source: str, dest: str) -> bool:

    if os.path.isfile(source):
        cmd = 'cp' + ' \'' + source + '\'' + ' \'' + dest + '\''
        process = subprocess.Popen(args=cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        stdout = stdout.decode('utf-8')
        stderr = stderr.decode('utf-8')

        return len(stderr) == 0

    return False


def generate_item(index: int, icon_image: QPixmap, name: str, is_dir: bool, descript: str, callback, parent) -> None:

    icon = QLabel()
    filename = QLabel()
    description = QLabel()
    access = QPushButton()

    filename.setStyleSheet('letter-spacing:0.5px;')
    description.setStyleSheet('color:#7A7A7A; letter-spacing:0.5px;')
    access.setFixedWidth(30)
    access.setFixedHeight(30)

    filename.setText(name)
    description.setText(descript)

    if icon_image is not None:
        icon.setPixmap(icon_image)

    if is_dir:
        if icon_image is None:
            icon.setPixmap(create_image_thumbnail(RESOURCE_PATH + 'images/directory.png'))

        access.setText('>')
        access.clicked.connect(callback)
        access.setProperty('type', 'directory')
        access.setProperty('dir_name', name)
        parent.addWidget(access, index, 2, 2, 1, Qt.AlignmentFlag.AlignRight and Qt.AlignmentFlag.AlignHCenter)
    else:
        if icon_image is None:
            icon.setPixmap(create_image_thumbnail(RESOURCE_PATH + 'images/file.png'))

        access.setText('=')
        access.clicked.connect(callback)
        access.setProperty('type', 'file')
        access.setProperty('filename', name)
        parent.addWidget(access, index, 2, 2, 1, Qt.AlignmentFlag.AlignRight and Qt.AlignmentFlag.AlignHCenter)

    parent.addWidget(icon, index, 0, 2, 1, Qt.AlignmentFlag.AlignLeft and Qt.AlignmentFlag.AlignHCenter)
    parent.addWidget(filename, index, 1, 1, 1, Qt.AlignmentFlag.AlignLeft and Qt.AlignmentFlag.AlignBottom)
    parent.addWidget(description, index + 1, 1, 1, 1, Qt.AlignmentFlag.AlignLeft and Qt.AlignmentFlag.AlignTop)


class ScreenCastUpdate(QThread):

    def __init__(self, adbc: Adb, is_running: bool, label_screenshot: QLabel, get_window_size: callable, parent = None):

        super().__init__(parent)

        self.adbc = adbc
        self.is_running = is_running
        self.label_screenshot = label_screenshot
        self.get_window_size = get_window_size


    def run(self):

        while self.is_running:
            image = self.adbc.screenshot()

            if image is None:
                show_message('Failed to capture screen! Please check connection.', 'Failed to capture screenshot')
                break

            else:
                dimension = list(image.shape[1::-1])
                window_size = self.get_window_size()

                # Fit with window height.
                if window_size[1] / dimension[1] * dimension[0] <= window_size[0]:
                    scale_factor = window_size[1] / dimension[1]

                # Fit with window width.
                else:
                    scale_factor = window_size[0] / dimension[0]

                dimension[0] = int(dimension[0] * scale_factor)
                dimension[1] = int(dimension[1] * scale_factor)

                image = cv2.resize(image, dimension)

                height, width, channel = image.shape
                bytesPerLine = 3 * width
                q_image = QImage(image, width, height, bytesPerLine, QImage.Format.Format_RGB888)

                self.label_screenshot.setPixmap(QPixmap.fromImage(q_image))

            sleep(0.001)


class ScreenCast(QMainWindow):

    def __init__(self, adbc, parent=None):

        super().__init__(parent)

        self.adbc = adbc
        self.is_running = True

        self.label_screenshot = QLabel('')
        self.label_screenshot.setStyleSheet('background-color: #000000;')
        self.label_screenshot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.label_screenshot.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.vbox_layout = QVBoxLayout()
        self.vbox_layout.setContentsMargins(0, 0, 0, 0)
        self.vbox_layout.setSpacing(0)
        self.vbox_layout.addWidget(self.label_screenshot)

        self.widget_mainSection = QWidget()
        self.widget_mainSection.setLayout(self.vbox_layout)

        self.setCentralWidget(self.widget_mainSection)
        self.setMinimumWidth(300)
        self.setMinimumHeight(300)
        self.setWindowTitle("Android Live Cast")
        self.setWindowIcon(QIcon(RESOURCE_PATH + 'images/icon.png'))

        self.update_thread = ScreenCastUpdate(self.adbc, self.is_running, self.label_screenshot, self.get_window_size)


    def reset(self) -> None:

        self.is_running = True
        self.label_screenshot.setPixmap(QPixmap(RESOURCE_PATH + 'images/stream_waiting.png'))
        self.update_thread.start()
        self.show()


    def get_window_size(self) -> list:

        return [self.width(), self.height()]


    def closeEvent(self, event):

            self.is_running = False


class AdbGui(QMainWindow):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.devices = []
        self.device_items = []
        self.device_id = ''
        self.device_path = ''
        self.adbc = Adb()
        self.local_path = os.path.expanduser('~')
        self.sc = ScreenCast(self.adbc)

        if not self.local_path.endswith('/'):
            self.local_path += '/'

        if os.path.isdir(self.local_path + 'Desktop'):
            self.local_path += 'Desktop/'

        self.menubar = QMenuBar()
        self.menuItem_operation = self.menubar.addMenu('Operation')
        self.menuItem_devices = self.menubar.addMenu('Device')
        self.menuItem_tools = self.menubar.addMenu('Tools')
        self.menuItem_help = self.menubar.addMenu('Help')

        self.menuItem_operation.addAction('Reload device list', self.load_devices)
        self.menuItem_operation.addAction('Reload device file explorer', self.load_remote)
        self.menuItem_operation.addAction('Reload local file explorer', self.load_local)

        self.menuItem_tools.addAction('Screen Cast', self.cast)

        self.menuItem_help.addAction('Get online document', self.visit_website)
        self.menuItem_help.addAction('About', self.show_about)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

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
        self.setWindowIcon(QIcon(RESOURCE_PATH + 'images/icon.png'))

        if not is_server_startup():
            show_message(
                'Adb server is NOT startup. Please start it manually.\nYou can run \"adb start-server\" in terminal to start it.',
                'Adb server not startup',
                LogType.ERROR
            )

            QCoreApplication.exit()

        self.load_devices()
        self.load_local()

        self.statusBar.showMessage('Ready')


    def load_devices(self) -> None:

        self.statusBar.showMessage('Loading device list ......')

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

        self.statusBar.showMessage('Device list loaded', STATUSBAR_MESSAGE_TIMEOUT_MS)


    def select_device(self):

        device_id = self.sender().text()
        self.clear()

        self.statusBar.showMessage('Connecting to device: ' + device_id + ' ......')

        if self.adbc.connect(device_id):

            self.statusBar.showMessage('Connected to device: ' + device_id)

            self.device_id = device_id
            self.device_path = '/'

            if self.adbc.is_path_exists(DEFAULT_REMOTE_PATH):
                self.device_path = DEFAULT_REMOTE_PATH

            for item in self.device_items:
                if item.text() == self.device_id:
                    item.setIcon(QIcon(RESOURCE_PATH + 'images/checked.png'))
                else:
                    item.setIcon(QIcon())

            self.load_remote()

        else:
            self.statusBar.showMessage('Failed to load device list')

            show_message(
                'Failed to connect to device: ' + device_id + '.\nPlease reload device list or reconnect device by adb command.',
                'Failed to connect to device',
                LogType.ERROR
            )


    def load_remote(self):

        self.statusBar.showMessage('Loading device files and directories ......')

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

            generate_item(index, create_image_thumbnail(RESOURCE_PATH + 'images/back.png'), '..', True, 'Back to parent directory', self.access_remote_directory, gridLayout_remoteSection)
            index += 2

            for c in content:
                if type(c) is File:
                    thumbnail = None

                    # Create thumbnail for image.
                    for extname in IMAGE_EXTENSION_NAME:
                        if c.get_fullname().lower().endswith(extname.lower()):
                            if self.adbc.pull(c.get_path_fullname(), PREVIEW_PATH):
                                thumbnail = create_image_thumbnail(PREVIEW_PATH, c.get_path_fullname())
                            else:
                                log('Failed to pull file for preview: ' + c.get_path_fullname(), LogType.ERROR)

                            break

                    # Create thumbnail for video.
                    for extname in VIDEO_EXTENSION_NAME:
                        if c.get_fullname().lower().endswith(extname.lower()):
                            if self.adbc.pull(c.get_path_fullname(), PREVIEW_PATH):
                                thumbnail = create_video_thumbnail(PREVIEW_PATH, c.get_path_fullname())
                            else:
                                log('Failed to pull file for preview: ' + c.get_path_fullname(), LogType.ERROR)

                            break

                    descript = 'File | ' + readable_size(c.get_size()) + ' | ' + c.get_datetime()
                    generate_item(index, thumbnail, c.get_fullname(), False, descript, self.access_remote_directory, gridLayout_remoteSection)

                    remove_thumbnail()
                else:
                    items_count = len(self.adbc.get_directory_struct(c.get_path_dirname()).get_content())
                    descript = 'Directory | ' + str(items_count) + ' items | ' + c.get_datetime()
                    generate_item(index, None, c.get_basename(), True, descript, self.access_remote_directory, gridLayout_remoteSection)

                index += 2

            gridLayout_remoteSection.addItem(QSpacerItem(10, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding), index, 0, 1, 3)

        widget_remoteSection.setLayout(gridLayout_remoteSection)
        self.scrollArea_remote.setWidget(widget_remoteSection)

        self.statusBar.showMessage('Device files and directories loaded')


    def load_local(self):

        self.statusBar.showMessage('Loading local files and directories ......')

        self.label_localLocation.setText('Local: ' + self.local_path)

        gridLayout_localSection = QGridLayout()
        widget_localSection = QWidget()

        gridLayout_localSection.setSpacing(10)
        gridLayout_localSection.setColumnStretch(0, 1)
        gridLayout_localSection.setColumnStretch(1, 10)
        gridLayout_localSection.setColumnStretch(2, 1)

        index = 0

        try:
            content = os.listdir(self.local_path)
        except PermissionError:
            content = []
            log('Failed to list directory: "' + self.local_path + '" due to permission error.', LogType.ERROR)

        generate_item(index, create_image_thumbnail(RESOURCE_PATH + 'images/back.png'), '..', True, 'Back to parent directory', self.access_local_directory, gridLayout_localSection)
        index += 2

        for c in content:
            path_filename = self.local_path + c

            if os.path.isfile(path_filename):
                thumbnail = None

                # Create thumbnail for image.
                for extname in IMAGE_EXTENSION_NAME:
                    if c.lower().endswith(extname.lower()):
                        thumbnail = create_image_thumbnail(path_filename)

                        break

                # Create thumbnail for video.
                for extname in VIDEO_EXTENSION_NAME:
                    if c.lower().endswith(extname.lower()):
                        thumbnail = create_video_thumbnail(path_filename)

                        break

                file_size = readable_size(os.path.getsize(path_filename))
                file_modified = datetime.fromtimestamp(os.path.getmtime(path_filename)).strftime('%Y.%m.%d %H:%M:%S')
                descript = 'File | ' + file_size + ' | ' + file_modified
                generate_item(index, thumbnail, c, False, descript, self.access_local_directory, gridLayout_localSection)

                remove_thumbnail()

            elif os.path.isdir(path_filename):
                try:
                    items_count = len(os.listdir(path_filename))
                except PermissionError:
                    items_count = 0
                    log('Failed to list directory: "' + path_filename + '" due to permission error.', LogType.ERROR)

                file_modified = datetime.fromtimestamp(os.path.getmtime(path_filename)).strftime('%Y.%m.%d %H:%M:%S')
                descript = 'Directory | ' + str(items_count) + ' items | ' + file_modified
                generate_item(index, None, c, True, descript, self.access_local_directory, gridLayout_localSection)

            index += 2

        gridLayout_localSection.addItem(QSpacerItem(10, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding), index, 0, 1, 3)

        widget_localSection.setLayout(gridLayout_localSection)
        self.scrollArea_local.setWidget(widget_localSection)

        self.statusBar.showMessage('Local files and directories loaded')


    def access_remote_directory(self):

        self.statusBar.showMessage('Accessing directory on device ......')

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

            self.statusBar.showMessage('Pulling file from "' + (self.device_path + filename) + '" to "' + (self.local_path + filename) + '"')

            if self.adbc.pull(self.device_path + filename, self.local_path + filename):
                self.load_local()

                self.statusBar.showMessage('Successfully pulled a file from "' + (self.device_path + filename) + '" to "' + (self.local_path + filename) + '"')
            else:
                self.load_remote()

                log_msg = 'Failed to pull file from device "' + (self.device_path + filename) + '" to local "' + (self.local_path + filename) + '"'

                log(log_msg, LogType.ERROR)

                self.statusBar.showMessage('Failed to pull a file from "' + (self.device_path + filename) + '" to "' + (self.local_path + filename) + '"')

                show_message(
                    log_msg,
                    'Failed to pull from device',
                    LogType.ERROR
                )

        self.statusBar.showMessage('Directory on device is loaded')


    def access_local_directory(self):

        self.statusBar.showMessage('Accessing directory on local ......')

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

            self.statusBar.showMessage('Pushing file from "' + (self.local_path + filename) + '" to "' + (self.device_path + filename) + '"')

            if self.adbc.push(self.local_path + filename, self.device_path + filename):
                self.load_remote()

                self.statusBar.showMessage('Successfully pushed a file from "' + (self.local_path + filename) + '" to "' + (self.device_path + filename) + '"')
            else:
                self.load_local()

                log_msg = 'Failed to push file from local, "' + (self.local_path + filename) + '" to device, "' + (self.device_path + filename) + '"'

                log(log_msg, LogType.ERROR)

                self.statusBar.showMessage('Failed to push a file from "' + (self.local_path + filename) + '" to "' + (self.device_path + filename) + '"')

                show_message(
                    log_msg,
                    'Failed to push to device',
                    LogType.ERROR
                )

        self.statusBar.showMessage('Directory on local is loaded')


    def cast(self):

        self.sc.reset()


    def visit_website(self):

        QDesktopServices.openUrl(QUrl('https://github.com/haward79/adb_gui'))


    def show_about(self):

        show_message(
            'Adb GUI is a GUI wrapper for adb.\n\nCurrent version is v1.0.0',
            'About this program',
            LogType.INFO
        )


    def clear(self):

        self.sc.is_running = False
        self.sc.hide()


    def closeEvent(self, event):

        self.clear()


app = QApplication(sys.argv)
window = AdbGui()

window.show()

sys.exit(app.exec())
