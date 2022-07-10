
from ppadb.client import Client as AdbClient
from log import *
from filesystem import *


_client = AdbClient(host="127.0.0.1", port=5037)


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


    def get_directory_struct(self, path_filename: str) -> DirectoryStruct:

        ds = DirectoryStruct()

        ds.parse(path_filename)
        path_filename = ds.get_path_dirname()

        if self._device is not None:
            resp = self._device.shell('ls -l ' + path_filename)

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
                            date_time = ' '.join([parts[5], parts[6]])
                            filename = ''.join(parts[7:])

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
                                    dir = Directory(path_filename + filename)
                                    ds.append_content(dir)

                                # File or symbolic link file.
                                else:
                                    file = File(path_filename + filename, size)
                                    ds.append_content(file)

        else:
            raise DeviceNotSpecify

        return ds


class DeviceNotSpecify(Exception):

    def __init__(self, message: str = 'Device NOT connected. Please run connect() first!'):

        pass
