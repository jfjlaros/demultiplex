import md5
import StringIO


def md5_check(data, md5sum):
    return md5.md5(data).hexdigest() == md5sum


def make_fake_file(name, content):
    handle = StringIO.StringIO()
    handle.name = name
    handle.writelines(content)
    handle.seek(0)
    return handle


class FakeOpen(object):
    def __init__(self):
        self.handles = {}

    def open(self, name, attr=''):
        """Open a fake file.
        
        This handle can not be closed because we want to inspect the content
        even after close() was called.

        :arg str name: Name of the file.
        :arg str attr: Open attributes (ignored).

        :returns stream: Fake file handle.
        """
        handle = StringIO.StringIO()
        handle.name = name
        handle.close = lambda: None
        self.handles[name] = handle
        return handle
