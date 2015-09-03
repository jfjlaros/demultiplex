#!/usr/bin/python

"""
Split a FASTA/FASTQ file on barcode.


If a file containing barcodes is given, the options concerning guessing the
barcodes (AMOUNT and SIZE) will be ignored.

Use the location (-r) if the barcode is not in the header, but in the read. The
positions are one-based and inclusive.

Format of the barcode file:
name barcode
"""

import argparse
import Levenshtein
import sys

from Bio import SeqIO
from collections import defaultdict

from .fastools import guess_file_format
from . import version


class Demultiplex(object):
    """
    Demultiplex an NGS data file.
    """
    def __init__(self, handle, barcodes, mismatch, amount, size, loc, read, f,
            header_x):
        """
        Initialise the class.

        :arg stream handle: Open readable handle to an NGS data file.
        :arg stream barcodes: Open readable handle to a file containing
            barcodes.
        :arg int mismatch: Number of allowed mismatches in the barcodes.
        :arg int amount: Number of barcodes.
        :arg int size: Number of records to probe.
        :arg tuple(int, int) loc: Location of the barcode in a read.
        :arg tuple(int, int) read: Location of the read.
        :arg function f: A pairwise distance function.
        :arg bool header_x: Use HiSeq X header.
        """
        self._handle = handle
        self._mismatch = mismatch
        self._location = loc
        self._read = read
        self._names = []
        self._f = f
        self._file_format = guess_file_format(handle)
        self.get_barcode = self._get_barcode_from_header

        if header_x:
            self.get_barcode = self._get_barcode_from_header_x

        if loc:
            self.get_barcode = self._get_barcode_from_read
            self._location[0] -= 1

        if not read:
            if loc:
                self._read = loc[1], 9999999
        else:
            self._read[0] -= 1

        if barcodes:
            self._names, self._barcodes = zip(*map(lambda x:
                x.strip().split(), barcodes.readlines()))
        else:
            self._barcodes = self.guess_barcodes(amount, size)

        self.demultiplex()


    def _get_barcode_from_header(self, record):
        """
        Extract the barcode from the header of a FASTA/FASTQ record.

        :arg object record: Fastq record.

        :returns tuple(str, object): A tuple containing the barcode and the
            record.
        """
        return record, record.id.split('#')[1].split('/')[0]


    def _get_barcode_from_header_x(self, record):
        """
        Extract the barcode from the header of a FASTA/FASTQ record, for files
        created with a HiSeq X.

        :arg object record: Fastq record.

        :returns tuple(str, object): A tuple containing the barcode and the
            record.
        """
        return record, record.description.split(':')[-1]


    def _get_barcode_from_read(self, record):
        """
        Extract the barcode from the sequence of a FASTA/FASTQ record.

        :arg object record: Fastq record.

        :returns tuple(str, object): A tuple containing the barcode and the
            record.
        """
        return (record[self._read[0]:self._read[1]],
            str(record.seq[self._location[0]:self._location[1]]))


    def guess_barcodes(self, amount, size):
        """
        Find the most abundant barcodes in a FASTA/FASTQ file.

        After use, the input stream is rewinded.

        :arg int amount: Number of barcodes.
        :arg int size: Number of records to probe.

        :returns list: List of barcodes.
        """
        barcode = defaultdict(int)
        records_read = 0

        for record in SeqIO.parse(self._handle, self._file_format):
            barcode[self.get_barcode(record)[1]] += 1

            if records_read > size:
                break
            records_read += 1

        self._handle.seek(0)

        return sorted(barcode, key=barcode.get)[::-1][:amount]


    def demultiplex(self):
        """
        Demultiplex a FASTA/FASTQ file.
        """
        output_handle = {}

        filename, _, ext = self._handle.name.rpartition('.')
        default_handle = open("%s_%s.%s" % (filename, "UNKNOWN", ext), "w")

        # Create the output files in a dictionary indexed by barcode.
        for i in self._barcodes:
            name = i

            if self._names:
                name = self._names[self._barcodes.index(i)]

            output_handle[i] = open("%s_%s.%s" % (filename, name, ext), "w")

        for record in SeqIO.parse(self._handle, self._file_format):
            new_record, barcode = self.get_barcode(record)

            # Find the closest barcode.
            distance = map(lambda x: self._f(x, barcode), self._barcodes)
            min_distance = min(distance)

            if min_distance <= self._mismatch:
                SeqIO.write(new_record, output_handle[self._barcodes[
                    distance.index(min_distance)]], self._file_format)
            else:
                SeqIO.write(new_record, default_handle, self._file_format)


def main():
    """
    Main entry point.
    """
    usage = __doc__.split("\n\n\n")
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=usage[0],
        epilog=usage[1])

    parser.add_argument('-i', dest='input', type=argparse.FileType('r'),
        default=sys.stdin, help='input file (default=<stdin>)')
    parser.add_argument('-b', dest='barcodes', type=argparse.FileType('r'),
        help='file containing barcodes')
    parser.add_argument('-a', dest='amount', type=int, default=12,
        help='amount of barcodes (%(type)s default: %(default)s)')
    parser.add_argument('-s', dest='size', type=int, default=1000000,
        help='sample size (%(type)s default: %(default)s)')
    parser.add_argument('-m', dest='mismatch', type=int, default=1,
        help='number of mismatches (%(type)s default: %(default)s)')
    parser.add_argument('-l', dest='location', type=int, default=[],
        nargs=2, help='location of the barcode')
    parser.add_argument('-r', dest='selection', type=int, default=[],
        nargs=2, help='selection of the read')
    parser.add_argument('-H', dest='dfunc', default=False,
        action="store_true", help="use Hamming distance")
    parser.add_argument('-x', dest='header_x', default=False,
        action="store_true", help='use HiSeq X header format')
    parser.add_argument('-v', action="version", version=version(parser.prog))

    args = parser.parse_args()

    dfunc = Levenshtein.distance
    if args.dfunc:
        dfunc = Levenshtein.hamming

    Demultiplex(args.input, args.barcodes, args.mismatch, args.amount,
        args.size, args.location, args.selection, dfunc, args.header_x)


if __name__ == "__main__":
    main()
