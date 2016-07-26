"""
Tests for demultiplex.
"""
import Levenshtein

from fastools import demultiplex

from shared import FakeOpen, md5_check


class TestCLI(object):
    def setup(self):
        self._fake_open = FakeOpen()
        demultiplex.open = self._fake_open.open

        self._input = open('data/demultiplex.fq')
        self._barcodes = open('data/barcodes.txt')

    def _md5_check(self, fileno, md5sum):
        return md5_check(self._fake_open.handles[fileno].getvalue(), md5sum)

    def test_from_file(self):
        demultiplex.Demultiplex(
            self._input, self._barcodes, 0, 0, 0, (), (), Levenshtein.distance,
            True).demultiplex()
        assert self._md5_check(0, 'd41d8cd98f00b204e9800998ecf8427e')
