
from enum import Enum
from PyQt6.QtWidgets import QMessageBox


_log_msg = ''


class LogType(Enum):

    INFO = 0
    ERROR = 1


def log(msg: str, log_type: LogType = LogType.INFO):

    global _log_msg

    msg_formatted = log_type.name + '> ' + msg

    print(msg_formatted)

    _log_msg += msg_formatted + '\n'


def write_log(filename: str):

    global _log_msg

    with open(filename, 'w') as fout:
        fout.write(_log_msg)

    _log_msg = ''


def show_message(msg: str, title: str, log_type: LogType = LogType.INFO):

    msg_box = QMessageBox()
    msg_box.setWindowTitle(title)

    if log_type is LogType.ERROR:
        msg_box.setIcon(QMessageBox.Icon.Critical)
    else:
        msg_box.setIcon(QMessageBox.Icon.Information)

    msg_box.setText(msg)

    msg_box.exec()
