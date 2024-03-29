
from os import path
import io
import numpy as np
import cv2
from PIL import Image
from ppadb.client import Client as AdbClient
from log import *
from filesystem import *


_client = AdbClient(host="127.0.0.1", port=5037)


def is_server_startup() -> bool:

    try:
        _client.devices()
    except:
        pass
    else:
        return True

    return False


def device_list() -> list:

    devices_list = []

    try:
        devices = _client.devices()
    except RuntimeError as e:
        log('Try to list devices, but encountered an error:\n' + str(e), LogType.ERROR)
        exit(1)

    for device in devices:
        devices_list.append(device.get_serial_no())

    return devices_list


def handle_deviceNotSpecify() -> None:

    log_msg = 'Unable to do the request due to no device is connected.\nPlease select a device from device item in menu bar.'

    log(log_msg, LogType.ERROR)
    show_message(log_msg, 'Device not connected', LogType.ERROR)


class Adb:

    def __init__(self, device_id: str = None):

        self._device = None

        if device_id is not None:
            self.connect(device_id)


    def connect(self, device_id: str) -> bool:

        if device_id in device_list():
            self._device = _client.device(device_id)
        else:
            log('Device is NOT connected to adb server.', LogType.ERROR)

        return self._device is not None


    def is_path_exists(self, path: str) -> bool:

        if self._device is not None:
            resp = self._device.shell('ls -l \'' + path + '\'')

            return resp.lower().find('no such file or directory') == -1

        else:
            handle_deviceNotSpecify()

            return False


    def get_directory_struct(self, path_filename: str) -> DirectoryStruct:

        ds = DirectoryStruct()

        ds.parse(path_filename)
        path_filename = ds.get_path_dirname()

        if self._device is not None:
            resp = self._device.shell('ls -l -L \'' + path_filename + '\'')

            if resp.lower().find('no such file or directory') != -1:
                log('No such path: ' + path_filename, LogType.ERROR)

            else:
                for line in resp.split('\n'):
                    if line.find('Permission denied') != -1:
                        log(line, LogType.ERROR)
                    else:
                        if line.startswith('total '):
                            pass
                        else:
                            parts = line.split()

                            if len(parts) >= 7:
                                permission = parts[0]
                                owner = parts[2]
                                group = parts[3]
                                size = parts[4]
                                date_time = ' '.join([parts[5], parts[6]]).replace('-', '.')
                                filename = ''.join(parts[7:]).replace('\\', ' ')
                                link = ''

                                if size.find('?') == -1:
                                    size = int(size)
                                else:
                                    size = -1

                                pos = filename.find('->')
                                if pos != -1:
                                    link = filename[pos+2:]
                                    filename = filename[:pos]

                                if permission.find('?') == -1:
                                    # Directory.
                                    if permission.startswith('d'):
                                        dir = Directory(path_filename + filename, date_time, owner, group, permission[1:])
                                        ds.append_content(dir)

                                    # File or symbolic link file.
                                    else:
                                        file = File(path_filename + filename, size, date_time, owner, group, permission[1:])
                                        ds.append_content(file)

        else:
            handle_deviceNotSpecify()

        return ds


    def pull(self, source: str, dest: str) -> bool:

        if self._device is not None:
            if self.is_path_exists(source):
                self._device.pull(source, dest)

                return True

            return False

        else:
            handle_deviceNotSpecify()


    def push(self, source: str, dest: str) -> bool:

        if self._device is not None:
            if path.isfile(source):
                self._device.push(source, dest)

                return True

            return False

        else:
            handle_deviceNotSpecify()


    def screenshot(self) -> np.ndarray:

        if self._device is not None:
            image_string = self._device.screencap()
            image = Image.open(io.BytesIO(image_string))
            image = np.asarray(image)
            image = cv2.cvtColor(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), cv2.COLOR_BGR2RGB)

            return image

        else:
            handle_deviceNotSpecify()
