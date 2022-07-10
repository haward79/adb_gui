
from typing import Union


def readable_size(size: int) -> str:

    UNIT = ('Byte', 'KB', 'MB', 'GB', 'TB')

    if size >= 0:
        level = 0
        while size >= 1024:
            level += 1
            size /= 1024

        return '{:.2f}'.format(size) + ' ' + UNIT[level]
    else:
        return ''


class File:

    def __init__(self, path_fullname: str = None, size: int = -1, date_time: str = '', owner: str = '', group: str = '', permission: str = ''):

        self._path = ''
        self._basename = ''
        self._extname = ''
        self._size = 0
        self._datetime = ''
        self._owner = ''
        self._group = ''
        self._permission = ''

        self.parse(path_fullname, size, date_time, owner, group, permission)


    def get_path(self) -> str:

        return self._path


    def get_basename(self) -> str:

        return self._basename


    def get_extname(self) -> str:

        return self._extname


    def get_fullname(self) -> str:

        if len(self._extname) > 0:
            return self._basename + '.' + self._extname
        else:
            return self._basename


    def get_path_fullname(self) -> str:

        return self._path + self.get_fullname()


    def get_size(self) -> int:

        return self._size


    def get_datetime(self) -> str:

        if len(self._datetime) == 0:
            return '--------'
        else:
            return self._datetime


    def get_owner(self) -> str:

        return self._owner


    def get_group(self) -> str:

        return self._group


    def get_permission(self) -> str:

        if len(self._permission) == 0:
            return '--- --- ---'
        else:
            return self._permission


    def parse(self, path_fullname: str = None, size: int = -1, date_time: str = '', owner: str = '', group: str = '', permission: str = '') -> None:

        self._path = ''
        self._basename = ''
        self._extname = ''
        self._size = 0
        self._datetime = date_time
        self._owner = owner
        self._group = group
        self._permission = permission

        if path_fullname is not None:
            ext_pos = path_fullname.rfind('.')
            last_slash_pos = path_fullname.rfind('/')

            if last_slash_pos is None:
                self._path = './'
            else:
                self._path = path_fullname[:last_slash_pos+1]

            if ext_pos is not None and ext_pos > last_slash_pos:
                self._basename = path_fullname[last_slash_pos+1:ext_pos]
                self._extname = path_fullname[ext_pos+1:]
            else:
                self._basename = path_fullname[last_slash_pos+1:]

            if size >= 0:
                self._size = size
            else:
                self._size = -1


class Directory:

    def __init__(self, path_fullname: str = None, date_time: str = '', owner: str = '', group: str = '', permission: str = ''):

        self._basename = ''
        self._path = ''
        self._datetime = date_time
        self._owner = owner
        self._group = group
        self._permission = permission

        self.parse(path_fullname, date_time, owner, group, permission)


    def get_basename(self) -> str:

        return self._basename


    def get_path(self) -> str:

        return self._path


    def get_path_dirname(self) -> str:

        if self._basename is None:
            return self._path
        else:
            return self._path + self._basename + '/'


    def get_datetime(self) -> str:

        if len(self._datetime) == 0:
            return '--------'
        else:
            return self._datetime


    def get_owner(self) -> str:

        return self._owner


    def get_group(self) -> str:

        return self._group


    def get_permission(self) -> str:

        if len(self._permission) == 0:
            return '--- --- ---'
        else:
            return self._permission


    def parse(self, path_fullname: str = None, date_time: str = '', owner: str = '', group: str = '', permission: str = '') -> None:

        self._basename = ''
        self._path = ''
        self._datetime = date_time
        self._owner = owner
        self._group = group
        self._permission = permission

        if path_fullname is not None:
            if path_fullname == '/':
                self._path = '/'
                self._basename = None

            else:
                if path_fullname.endswith('/'):
                    path_fullname = path_fullname[:-1]

                last_slash_pos = path_fullname.rfind('/')

                if last_slash_pos is None:
                    self._path = './'
                else:
                    self._path = path_fullname[:last_slash_pos+1]

                self._basename = path_fullname[last_slash_pos+1:]


class DirectoryStruct(Directory):

    def __init__(self, path_fullname: str = None, content: list = []):

        super().__init__(path_fullname)
        self._content = []

        self.set_content(content)


    def get_content(self) -> list:

        return self._content


    def append_content(self, content) -> None:

        if type(content) is list:
            for c in content:
                if type(c) is File or type(c) is Directory or type(c):
                    self._content.append(c)
        else:
            if type(content) is File or type(content) is Directory or type(content):
                self._content.append(content)


    def set_content(self, content: list) -> None:

        self._content = []
        self.append_content(content)


    def access(self, name: str) -> Union[File, Directory]:

        for c in self._content:
            if c.get_basename() == name:
                return c

        return None
