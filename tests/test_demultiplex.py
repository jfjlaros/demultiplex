"""
Tests for demultiplex.
"""
import md5
import Levenshtein
import StringIO

from fastools import demultiplex


class FakeOpen(object):
    def __init__(self):
        self.handles = []

    def open(self, name, attr=''):
        handle = StringIO.StringIO()
        handle.name = name
        self.handles.append(handle)
        return handle


class TestCLI(object):
    """
    """
    def setup(self):
        self._fake_open = FakeOpen()
        demultiplex.open = self._fake_open.open

        self._input = open('data/demultiplex.fq')
        self._barcodes = open('data/barcodes.txt')

    def _md5_check(self, fileno, md5sum):
        return md5.md5(
            self._fake_open.handles[fileno].getvalue()).hexdigest() == md5sum

    def test_from_file(self):
        demultiplex.Demultiplex(
            self._input, self._barcodes, 0, 0, 0, (), (), Levenshtein.distance,
            True).demultiplex()
        assert self._md5_check(0, 'd41d8cd98f00b204e9800998ecf8427e')
