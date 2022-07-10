
import sys
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QImage, QPixmap, QIcon, QAction, QDesktopServices
from PyQt6.QtWidgets import QApplication, QMessageBox, QMainWindow, QScrollArea, QWidget, QMenuBar, QLabel, QPushButton, QGridLayout, QVBoxLayout, QHBoxLayout
from filesystem import *
from adb import device_list, Adb
from log import *


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


class AdbGui(QMainWindow):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.devices = []
        self.device_items = []
        self.device_id = ''
        self.device_path = ''
        self.adbc = Adb()

        self.menubar = QMenuBar()
        self.menuItem_operation = self.menubar.addMenu('Operation')
        self.menuItem_devices = self.menubar.addMenu('Device')
        self.menuItem_help = self.menubar.addMenu('Help')

        self.menuItem_operation.addAction('Reload device list', self.load_devices)

        self.menuItem_help.addAction('Get online document', self.visit_website)
        self.menuItem_help.addAction('About', self.show_about)

        self.label_remoteLocation = QLabel('Remote: ')
        self.label_localLocation = QLabel('Local: ')

        self.hlayout_locationSection = QHBoxLayout()
        self.hlayout_locationSection.setContentsMargins(10, 10, 10, 0)
        self.hlayout_locationSection.setSpacing(0)
        self.hlayout_locationSection.addWidget(self.label_remoteLocation)
        self.hlayout_locationSection.addWidget(self.label_localLocation)

        self.scrollArea_remote = QScrollArea()
        self.scrollArea_local = QScrollArea()

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
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)
        self.setWindowTitle("Graphical User Interface for Adb")
        self.setWindowIcon(QIcon('images/icon.png'))

        self.load_devices()


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

            for item in self.device_items:
                if item.text() == self.device_id:
                    item.setIcon(QIcon('images/checked.png'))
                else:
                    item.setIcon(QIcon())

            self.load_remote()

        else:
            msg = QMessageBox()
            msg.setWindowTitle('Failed to connect to device')
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText('Failed to connect to device: ' + device_id + '.\nPlease reload device list or reconnect device by adb command.')

            msg.exec()


    def load_remote(self):

        self.label_remoteLocation.setText('Remote: ' + self.device_path)

        gridLayout_remoteSection = QGridLayout()
        widget_remoteSection = QWidget()

        gridLayout_remoteSection.setSpacing(10)

        if len(self.device_id) == 0 or len(self.device_path) == 0:
            pass

        else:
            index = 0
            content = self.adbc.get_directory_struct(self.device_path).get_content()

            for c in content:
                icon = QLabel()
                filename = QLabel()
                description = QLabel()

                icon.setPixmap(load_image('images/blank.png'))
                filename.setStyleSheet('letter-spacing:0.5px;')
                description.setStyleSheet('color:#7A7A7A; letter-spacing:0.5px;')

                if type(c) is File:
                    filename.setText(c.get_fullname())
                    description.setText('File | ' + str(c.get_size()) + ' Bytes')
                else:
                    filename.setText(c.get_basename())
                    description.setText('Directory')

                gridLayout_remoteSection.addWidget(icon, index, 0, 2, 1, Qt.AlignmentFlag.AlignLeft and Qt.AlignmentFlag.AlignHCenter)
                gridLayout_remoteSection.addWidget(filename, index, 1, 1, 1, Qt.AlignmentFlag.AlignLeft and Qt.AlignmentFlag.AlignBottom)
                gridLayout_remoteSection.addWidget(description, index + 1, 1, 1, 1, Qt.AlignmentFlag.AlignLeft and Qt.AlignmentFlag.AlignTop)

                index += 2

        widget_remoteSection.setLayout(gridLayout_remoteSection)
        self.scrollArea_remote.setWidget(widget_remoteSection)


    def load_local(self):

        self.label_localLocation.setText('Local: ')


    def visit_website(self):

        QDesktopServices.openUrl(QUrl('https://github.com/haward79/'))


    def show_about(self):

        msg = QMessageBox()
        msg.setWindowTitle('About this program')
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText('Adb GUI is a GUI wrapper for adb.\n\nCurrent version is v1.0.0')

        msg.exec()


app = QApplication(sys.argv)
window = AdbGui()

window.show()

sys.exit(app.exec())
