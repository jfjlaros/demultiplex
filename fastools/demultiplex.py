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

from .fastools import guessFileType
from . import version

class Demultiplex(object):
    """
    Demultiplex an NGS data file.
    """
    def __init__(self, handle, barcodes, mismatch, amount, size, loc, read, f):
        """
        Initialise the class.

        @arg handle: Open readable handle to an NGS data file.
        @type handle: stream
        @arg barcodes: Open readable handle to a file containing barcodes.
        @type barcodes: stream
        @arg mismatch: Number of allowed mismatches in the barcodes.
        @type mismatch: int
        @arg amount: Number of barcodes.
        @type amount: int
        @arg size: Number of records to probe.
        @type size: int
        @arg loc: Location of the barcode in a read.
        @type loc: tuple(int, int)
        @arg read: Location of the read.
        @type read: tuple(int, int)
        @arg f: A pairwise distance function.
        @type f: function
        """
        self.__handle = handle
        self.__mismatch = mismatch
        self.__location = loc
        self.__read = read
        self.__names = []
        self.__f = f
        self.__fileType = guessFileType(handle)
        self.getBarcode = self.__getBarcodeFromHeader

        if loc:
            self.getBarcode = self.__getBarcodeFromRead
            self.__location[0] -= 1
        #if

        if not read:
            if loc:
                self.__read = loc[1], 9999999
        #if
        else:
            self.__read[0] -= 1

        if barcodes:
            self.__names, self.__barcodes = zip(*map(lambda x:
                x.strip().split(), barcodes.readlines()))
        else:
            self.__barcodes = self.guessBarcodes(amount, size)

        self.demultiplex()
    #__init__

    def __getBarcodeFromHeader(self, record):
        """
        Extract the barcode from the header of a FASTA/FASTQ record.

        @arg record: Fastq record.
        @type record: object

        @returns: A tuple containing the barcode and the record.
        @rtype: (str, object)
        """
        return record, record.id.split('#')[1].split('/')[0]
    #__getBarcodeFromHeader

    def __getBarcodeFromRead(self, record):
        """
        Extract the barcode from the sequence of a FASTA/FASTQ record.

        @arg record: Fastq record.
        @type record: object

        @returns: A tuple containing the barcode and a selection of the record.
        @rtype: (str, object)
        """
        return (record[self.__read[0]:self.__read[1]],
            str(record.seq[self.__location[0]:self.__location[1]]))
    #__getBarcodeFromRead

    def guessBarcodes(self, amount, size):
        """
        Find the most abundant barcodes in a FASTA/FASTQ file.

        After use, the input stream is rewinded.

        @arg amount: Number of barcodes.
        @type amount: int
        @arg size: Number of records to probe.
        @type size: int

        @returns: List of barcodes.
        @rtype: list
        """
        barcode = defaultdict(int)
        recordsRead = 0

        for record in SeqIO.parse(self.__handle, self.__fileType):
            barcode[self.getBarcode(record)[1]] += 1

            if recordsRead > size:
                break
            recordsRead += 1
        #for
        self.__handle.seek(0)

        return sorted(barcode, key=barcode.get)[::-1][:amount]
    #guessBarcodes

    def demultiplex(self):
        """
        Demultiplex a FASTA/FASTQ file.
        """
        outputHandle = {}

        filename, _, ext = self.__handle.name.rpartition('.')
        defaultHandle = open("%s_%s.%s" % (filename, "UNKNOWN", ext), "w")

        # Create the output files in a dictionary indexed by barcode.
        for i in self.__barcodes:
            name = i

            if self.__names:
                name = self.__names[self.__barcodes.index(i)]

            outputHandle[i] = open("%s_%s.%s" % (filename, name, ext), "w")
        #for

        for record in SeqIO.parse(self.__handle, self.__fileType):
            newRecord, barcode = self.getBarcode(record)

            # Find the closest barcode.
            distance = map(lambda x: self.__f(x, barcode),
                self.__barcodes)
            minDistance = min(distance)

            if minDistance <= self.__mismatch:
                SeqIO.write(newRecord, outputHandle[self.__barcodes[
                    distance.index(minDistance)]], self.__fileType)
            else:
                SeqIO.write(newRecord, defaultHandle, self.__fileType)
        #for
    #demultiplex
#Demultiplex

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
    parser.add_argument('-v', action="version", version=version(parser.prog))

    args = parser.parse_args()

    dfunc = Levenshtein.distance
    if args.dfunc:
        dfunc = Levenshtein.hamming

    Demultiplex(args.input, args.barcodes, args.mismatch, args.amount,
        args.size, args.location, args.selection, dfunc)
#main

if __name__ == "__main__":
    main()
