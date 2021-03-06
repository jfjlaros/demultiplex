"""Tests for demultiplex."""
from io import StringIO

from demultiplex import cli
from fastools import guess_header_format
from jit_open import jit_open

from shared import FakeOpen, md5_check, make_fake_file


class TestCLI(object):
    def setup(self):
        fake_open = FakeOpen()
        self._handles = fake_open.handles
        jit_open.open = fake_open.open

        self._input = open('data/demultiplex.fq')
        self._input_x = open('data/demultiplex_x.fq')
        self._barcodes = open('data/barcodes.txt')
        self._matchcodes = open('data/matchcodes.txt')

    def _md5_check(self, name, md5sum):
        return md5_check(self._handles[name].getvalue(), md5sum)

    def test_amount_read(self):
        fake_file = StringIO()
        cli.guess(self._input, fake_file, True, None, 2, 5, 1000000, 4, False)
        assert fake_file.getvalue() == '1 AAAA\n2 CCCC\n3 GGGG\n4 TTTT\n'

    def test_x_amount(self):
        fake_file = StringIO()
        cli.guess(
            self._input, fake_file, False, None, None, None, 1000000, 1, False)
        assert fake_file.getvalue() == '1 ACTT\n'

    def test_from_file_mismatch_0(self):
        """Read barcodes from file, no mismatches.

        Result: file 1, 3 and UNKNOWN contain one read, file 4 contains two.
        """
        cli.demux(
            [self._input], self._barcodes, False, None, None, None, 0, True)
        assert len(self._handles) == 4
        assert self._md5_check(
            './demultiplex_UNKNOWN.fq', '7a2889d04b4e8514ca01ea6c75884cd6')

    def test_from_file_mismatch_1(self):
        """Read barcodes from file, one mismatch.

        Result: file 1-3 contain one read, file 4 contains two and UNKNOWN is
        empty. Notably file 2 is not empty although the barcode is shorter.
        """
        cli.demux(
            [self._input], self._barcodes, False, None, None, None, 1, True)
        assert len(self._handles) == 4
        assert self._md5_check(
            './demultiplex_2.fq', '7a2889d04b4e8514ca01ea6c75884cd6')

    def test_x_from_file_mismatch_0(self):
        """Read barcodes from file, no mismatches, HiSeq X headers.

        Result: file 1-3 contain one sequence, file 4 contains two and UNKNOWN
        is empty.
        """
        cli.demux(
            [self._input_x], self._barcodes, False, None, None, None, 0, True)
        assert len(self._handles) == 4
        assert self._md5_check(
            './demultiplex_x_1.fq', '3f013cddfedf1b5b1ad5d01913692333')
        assert self._md5_check(
            './demultiplex_x_4.fq', 'a044932ca48decaba985032ecf725753')

    def test_wrong_barcode_format(self):
        handle = make_fake_file('', 'ACTA\nACTC\nACTG\nACTT\n')
        try:
            cli.demux([self._input], handle, False, None, None, None, 0, False)
        except ValueError as error:
            assert str(error) == 'invalid barcodes file format'

    def test_guess_header_normal(self):
        assert guess_header_format(self._input) == 'normal'

    def test_guess_header_x(self):
        assert guess_header_format(self._input_x) == 'x'

    def test_guess_header_unknown(self):
        assert guess_header_format(
            make_fake_file('', '@name description\n')) == 'unknown'

    def test_match(self):
        """
        """
        cli.bcmatch(self._input, self._matchcodes, 1, False)
        assert len(self._handles) == 4
        assert self._md5_check(
            './demultiplex_1.fq', '5f8d00947e9a794b9ddf187de271ba6f')
        assert self._md5_check(
            './demultiplex_2.fq', '7a2889d04b4e8514ca01ea6c75884cd6')
        assert self._md5_check(
            './demultiplex_3.fq', '82aedd53845e523f92cf1cdb51cce80d')
        assert self._md5_check(
            './demultiplex_4.fq', '28803c1572714d178a1982143d8b7e8f')
