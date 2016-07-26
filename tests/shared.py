import md5
import StringIO


def md5_check(data, md5sum):
    return md5.md5(data).hexdigest() == md5sum


class FakeOpen(object):
    def __init__(self):
        self.handles = []

    def open(self, name, attr=''):
        handle = StringIO.StringIO()
        handle.name = name
        self.handles.append(handle)
        return handle
