"""
Tests for demultiplex.
"""
import Levenshtein

from fastools import demultiplex

from shared import FakeOpen, md5_check, make_fake_file


class TestCLI(object):
    def setup(self):
        fake_open = FakeOpen()
        self._handles = fake_open.handles
        demultiplex.open = fake_open.open

        self._input = open('data/demultiplex.fq')
        self._input_x = open('data/demultiplex_x.fq')
        self._barcodes = open('data/barcodes.txt')

    def _md5_check(self, name, md5sum):
        return md5_check(self._handles[name].getvalue(), md5sum)

    def test_from_file_mismatch_0(self):
        """
        Read barcodes from file, no mismatches.

        Result: file 1, 3 and UNKNOWN contain one read, file 4 contains two.
        """
        demultiplex.Demultiplex(
            self._input, self._barcodes, 0, 0, 0, (), (),
            Levenshtein.distance).demultiplex()
        assert len(self._handles) == 5
        assert self._md5_check(
            'data/demultiplex_UNKNOWN.fq', '7a2889d04b4e8514ca01ea6c75884cd6')
        assert self._md5_check(
            'data/demultiplex_2.fq', 'd41d8cd98f00b204e9800998ecf8427e')

    def test_from_file_mismatch_1(self):
        """
        Read barcodes from file, one mismatch.

        Result: file 1-3 contain one read, file 4 contains two and UNKNOWN is
        empty. Notably file 2 is not empty although the barcode is shorter.
        """
        demultiplex.Demultiplex(
            self._input, self._barcodes, 1, 0, 0, (), (),
            Levenshtein.distance).demultiplex()
        assert len(self._handles) == 5
        assert self._md5_check(
            'data/demultiplex_UNKNOWN.fq', 'd41d8cd98f00b204e9800998ecf8427e')
        assert self._md5_check(
            'data/demultiplex_2.fq', '7a2889d04b4e8514ca01ea6c75884cd6')

    def test_amount_read_mismatch_0(self):
        """
        Determine the most abundant barcode which is located in the read, no
        mismatches.

        Result: file AAAA, CCCC and GGGG contain one read, file TTTT contains
        two and UNKNOWN is empty.
        """
        demultiplex.Demultiplex(
            self._input, None, 0, 4, 1000000, (2, 5), (10, 100),
            Levenshtein.distance).demultiplex()
        assert len(self._handles) == 5
        assert self._md5_check(
            'data/demultiplex_UNKNOWN.fq', 'd41d8cd98f00b204e9800998ecf8427e')
        assert self._md5_check(
            'data/demultiplex_AAAA.fq', '1f488ff926d737170d3bd04bd2793d49')
        assert self._md5_check(
            'data/demultiplex_TTTT.fq', '499e4d04a5c7c6b5470345bba10c0d5b')

    def test_x_from_file_mismatch_0(self):
        """
        Read barcodes from file, no mismatches, HiSeq X headers.

        Result: file 1-3 contain one sequence, file 4 contains two and UNKNOWN
        is empty.
        """
        demultiplex.Demultiplex(
            self._input_x, self._barcodes, 0, 0, 0, (), (),
            Levenshtein.distance).demultiplex()
        assert len(self._handles) == 5
        assert self._md5_check(
            'data/demultiplex_x_UNKNOWN.fq',
            'd41d8cd98f00b204e9800998ecf8427e')
        assert self._md5_check(
            'data/demultiplex_x_1.fq', '3f013cddfedf1b5b1ad5d01913692333')
        assert self._md5_check(
            'data/demultiplex_x_4.fq', 'a044932ca48decaba985032ecf725753')

    def test_x_amount_mismatch_0(self):
        """
        Determine the most abundant barcode, no mismatches, HiSeq X headers.

        Result: file ACTT contains two sequences and UNKNOWN contains three.
        """
        demultiplex.Demultiplex(
            self._input_x, None, 0, 1, 1000000, (), (),
            Levenshtein.distance).demultiplex()
        assert len(self._handles) == 2
        assert self._md5_check(
            'data/demultiplex_x_UNKNOWN.fq',
            '74f352464842b07e15f08d150d43456d')
        assert self._md5_check(
            'data/demultiplex_x_ACTT.fq', 'a044932ca48decaba985032ecf725753')

    def test_x_amount_mismatch_1(self):
        """
        Determine the most abundant barcode, one mismatch, HiSeq X headers.

        Result: file ACTT contains five sequences and UNKNOWN is empty.
        """
        demultiplex.Demultiplex(
            self._input_x, None, 1, 1, 1000000, (), (),
            Levenshtein.distance).demultiplex()
        assert len(self._handles) == 2
        assert self._md5_check(
            'data/demultiplex_x_UNKNOWN.fq',
            'd41d8cd98f00b204e9800998ecf8427e')
        assert self._md5_check(
            'data/demultiplex_x_ACTT.fq', '14804d194a384503ae1fa35e6dba4818')

    def test_wrong_barcode_format(self):
        handle = make_fake_file('', 'ACTA\nACTC\nACTG\nACTT\n')
        try:
            demultiplex.Demultiplex(
                self._input, handle, 0, 0, 0, (), (), lambda x, y: 0)
        except ValueError, error:
            assert error[0] == 'invalid barcodes file format'

    def test_guess_header_normal(self):
        assert demultiplex.guess_header_format(self._input) == 'normal'

    def test_guess_header_x(self):
        assert demultiplex.guess_header_format(self._input_x) == 'x'

    def test_guess_header_unknown(self):
        assert demultiplex.guess_header_format(
            make_fake_file('', '@name description\n')) == 'unknown'
