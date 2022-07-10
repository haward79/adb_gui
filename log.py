
from enum import Enum


_log_msg = ''


class LogType(Enum):

    INFO = 0
    ERROR = 1


def log(msg: str, log_type: LogType = LogType.INFO):

    global _log_msg

    msg_formatted = log_type.name + '> ' + msg

    print(msg_formatted)
    _log_msg += msg_formatted


def write_log(filename: str):

    global _log_msg

    with open(filename, 'w') as fout:
        fout.write(_log_msg)

    _log_msg = ''
