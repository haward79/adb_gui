
from os import path
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

        resp = self._device.shell('ls -l \'' + path + '\'')

        return resp.lower().find('no such file or directory') == -1


    def get_directory_struct(self, path_filename: str) -> DirectoryStruct:

        ds = DirectoryStruct()

        ds.parse(path_filename)
        path_filename = ds.get_path_dirname()

        if self._device is not None:
            resp = self._device.shell('ls -l \'' + path_filename + '\'')

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

                                if size.find('?') == -1:
                                    size = int(size)
                                else:
                                    size = -1

                                pos = filename.find('->')
                                if pos != -1:
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
            raise DeviceNotSpecify

        return ds


    def pull(self, source: str, dest: str) -> bool:

        if self.is_path_exists(source):
            self._device.pull(source, dest)

            return True

        return False


    def push(self, source: str, dest: str) -> bool:

        if path.isfile(source):
            self._device.push(source, dest)

            return True

        return False


class DeviceNotSpecify(Exception):

    def __init__(self, message: str = 'Device NOT connected. Please run connect() first!'):

        pass
