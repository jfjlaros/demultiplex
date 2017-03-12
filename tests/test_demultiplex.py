"""
Tests for demultiplex.
"""
from StringIO import StringIO

from fastools import demultiplex

from shared import FakeOpen, md5_check, make_fake_file


class TestCLI(object):
    def setup(self):
        fake_open = FakeOpen()
        self._handles = fake_open.handles
        demultiplex.JITOpen = fake_open.open

        self._input = open('data/demultiplex.fq')
        self._input_x = open('data/demultiplex_x.fq')
        self._barcodes = open('data/barcodes.txt')

    def _md5_check(self, name, md5sum):
        return md5_check(self._handles[name].getvalue(), md5sum)

    def test_amount_read(self):
        """
        """
        fake_file = StringIO()
        demultiplex.guess(
            self._input, fake_file, True, 2, 5, 1000000, 4, False)
        assert fake_file.getvalue() == '1 TTTT\n2 AAAA\n3 CCCC\n4 GGGG\n'

    def test_x_amount(self):
        """
        """
        fake_file = StringIO()
        demultiplex.guess(
            self._input, fake_file, False, None, None, 1000000, 1, False)
        assert fake_file.getvalue() == '1 ACTT\n'

    def test_from_file_mismatch_0(self):
        """
        Read barcodes from file, no mismatches.

        Result: file 1, 3 and UNKNOWN contain one read, file 4 contains two.
        """
        demultiplex.demux(
            [self._input], self._barcodes, False, None, None, 0, True)
        assert len(self._handles) == 5
        assert self._md5_check(
            'demultiplex_UNKNOWN.fq', '7a2889d04b4e8514ca01ea6c75884cd6')
        assert self._md5_check(
            'demultiplex_2.fq', 'd41d8cd98f00b204e9800998ecf8427e')

    def test_from_file_mismatch_1(self):
        """
        Read barcodes from file, one mismatch.

        Result: file 1-3 contain one read, file 4 contains two and UNKNOWN is
        empty. Notably file 2 is not empty although the barcode is shorter.
        """
        demultiplex.demux(
            [self._input], self._barcodes, False, None, None, 1, True)
        assert len(self._handles) == 5
        assert self._md5_check(
            'demultiplex_UNKNOWN.fq', 'd41d8cd98f00b204e9800998ecf8427e')
        assert self._md5_check(
            'demultiplex_2.fq', '7a2889d04b4e8514ca01ea6c75884cd6')

    def test_x_from_file_mismatch_0(self):
        """
        Read barcodes from file, no mismatches, HiSeq X headers.

        Result: file 1-3 contain one sequence, file 4 contains two and UNKNOWN
        is empty.
        """
        demultiplex.demux(
            [self._input_x], self._barcodes, False, None, None, 0, True)
        assert len(self._handles) == 5
        assert self._md5_check(
            'demultiplex_x_UNKNOWN.fq', 'd41d8cd98f00b204e9800998ecf8427e')
        assert self._md5_check(
            'demultiplex_x_1.fq', '3f013cddfedf1b5b1ad5d01913692333')
        assert self._md5_check(
            'demultiplex_x_4.fq', 'a044932ca48decaba985032ecf725753')

    def test_wrong_barcode_format(self):
        handle = make_fake_file('', 'ACTA\nACTC\nACTG\nACTT\n')
        try:
            demultiplex.demux(
                [self._input], handle, False, None, None, 0, False)
        except ValueError, error:
            assert error[0] == 'invalid barcodes file format'

    def test_guess_header_normal(self):
        assert demultiplex.guess_header_format(self._input) == 'normal'

    def test_guess_header_x(self):
        assert demultiplex.guess_header_format(self._input_x) == 'x'

    def test_guess_header_unknown(self):
        assert demultiplex.guess_header_format(
            make_fake_file('', '@name description\n')) == 'unknown'
