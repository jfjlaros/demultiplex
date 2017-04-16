"""Split FASTA/FASTQ files on barcode.


Format of the barcode file:
name barcode
"""
import argparse
import sys

from collections import defaultdict
from os.path import basename, splitext

from Bio import SeqIO
from dict_trie import Trie
from jit_open import Handle, Queue

from .fastools import guess_file_format, guess_header_format
from .peeker import Peeker
from . import doc_split, version


_get_barcode = {
    'normal' : lambda record: record.id.split('#')[1].split('/')[0],
    'x': lambda record: record.description.split(':')[-1],
    'unknown': lambda record: record.seq}


class Extractor(object):
    def __init__(self, handle, in_read=False, start=None, end=None):
        """Configure a barcode extractor.

        :arg stream handle: Handle to an NGS data file.
        :arg bool in_read: Inspect the read instead of the header.
        :arg int start: Start of the barcode.
        :arg int end: End of the barcode.
        """
        self._start = start
        self._end = end

        if self._start:
            self._start -= 1

        self._get_barcode = _get_barcode['unknown']
        if not in_read:
            self._get_barcode = _get_barcode[guess_header_format(handle)]

    def get(self, record):
        return self._get_barcode(record)[self._start:self._end]


def count(handle, extractor, sample_size, threshold, use_freq=False):
    """Get the most frequent barcodes from an NGS data file.

    :arg stream handle: Handle to an NGS data file.
    :arg Extractor extractor: A barcode extractor.
    :arg int sample_size: Number of records to probe.
    :arg int threshold: Threshold for the selection method.
    :arg bool use_freq: Select frequent barcodes instead of a fixed amount.

    :returns list: A list of barcodes.
    """
    barcodes = defaultdict(int)

    for i, record in enumerate(SeqIO.parse(handle, guess_file_format(handle))):
        if i > sample_size:
            break
        barcodes[extractor.get(record)] += 1

    if use_freq:
        return filter(lambda x: barcodes[x] >= threshold, barcodes)
    return sorted(barcodes, key=barcodes.get, reverse=True)[:threshold]


def _open_files(filenames, barcode, queue):
    """For a list of input files, open the corresponding output files.

    :arg list filename: List of input filenames.
    :arg str barcode: Name of the barcode.
    :arg Queue queue: Queue for open files.

    :returns list: List of handles of output files.
    """
    handles = []

    for filename in filenames:
        base, ext = splitext(basename(filename))
        handles.append(Handle('{}_{}{}'.format(base, barcode, ext), queue))

    return handles


def _write(handles, records, file_format):
    for i, record in enumerate(records):
        SeqIO.write(record, handles[i], file_format)


def demultiplex(input_handles, barcodes_handle, extractor, mismatch, use_edit):
    """Demultiplex a list of NGS data files.

    :arg list input_handles: List of hanles to NGS data files.
    :arg stream barcodes_handle: Handle to a file containing barcodes.
    :arg Extractor extractor: A barcode extractor.
    :arg int mismatch: Number of allowed mismatches.
    :arg bool use_edit: Use Levenshtein distance instead of Hamming distance.
    """
    filenames = map(lambda x: x.name, input_handles)
    queue = Queue()
    default_handles = _open_files(filenames, 'UNKNOWN', queue)

    barcodes = {}
    for line in barcodes_handle.readlines():
        try:
            name, barcode = line.strip().split()
        except ValueError:
            raise ValueError('invalid barcodes file format')
        barcodes[barcode] = _open_files(filenames, name, queue)

    trie = Trie(barcodes.keys())
    distance_function = trie.best_hamming
    if use_edit:
        distance_function = trie.best_levenshtein

    file_format = guess_file_format(input_handles[0])
    readers = map(
        lambda x: SeqIO.parse(x, file_format), input_handles)

    while True:
        try:
            records = map(lambda x: x.next(), readers)
        except StopIteration:
            break

        barcode = distance_function(extractor.get(records[0]), mismatch)
        if barcode:
            _write(barcodes[barcode], records, file_format)
        else:
            _write(default_handles, records, file_format)

    queue.flush()


def guess(
        input_handle, output_handle, in_read, start, end,
        sample_size, threshold, use_freq):
    """Retrieve the most frequent barcodes.
    """
    extractor = Extractor(input_handle, in_read, start, end)
    barcodes = count(input_handle, extractor, sample_size, threshold, use_freq)

    for i, barcode in enumerate(barcodes):
        output_handle.write('{} {}\n'.format(i + 1, barcode))


def demux(
        input_handles, barcodes_handle, in_read, start, end, mismatch,
        use_edit):
    """Demultiplex any number of files given a list of barcodes.
    """
    extractor = Extractor(input_handles[0], in_read, start, end)
    demultiplex(input_handles, barcodes_handle, extractor, mismatch, use_edit)


def main():
    """Main entry point.
    """
    default_str = ' (default: %(default)s)'
    type_default_str = ' (%(type)s default: %(default)s)'

    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        '-r', dest='in_read', action='store_true',
        help='extract the barcodes from the read' + default_str)
    common_parser.add_argument(
        '-s', dest='start', type=int, default=None,
        help='start of the selection' + type_default_str)
    common_parser.add_argument(
        '-e', dest='end', type=int, default=None,
        help='end of the selection' + type_default_str)

    usage = __doc__.split('\n\n\n')
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=usage[0], epilog=usage[1])
    parser.add_argument('-v', action='version', version=version(parser.prog))
    subparsers = parser.add_subparsers(dest='subcommand')

    parser_guess = subparsers.add_parser(
        'guess', parents=[common_parser], description=doc_split(guess))
    parser_guess.add_argument(
        'input_handle', metavar='INPUT', type=argparse.FileType('r'),
        help='input file')
    parser_guess.add_argument(
        '-o', dest='output_handle', metavar='OUTPUT',
        type=argparse.FileType('w'), default=sys.stdout,
        help='output file (default: <stdout>)')
    parser_guess.add_argument(
        '-n', dest='sample_size', type=int, default=1000000,
        help='sample size' + type_default_str)
    parser_guess.add_argument(
        '-f', dest='use_freq', action='store_true',
        help='select on frequency instead of a fixed amount' + default_str)
    parser_guess.add_argument(
        '-t', dest='threshold', type=int, default=12,
        help='threshold for the selection method' + type_default_str)
    parser_guess.set_defaults(func=guess)

    parser_demux = subparsers.add_parser(
        'demux', parents=[common_parser],
        description=doc_split(demux))
    parser_demux.add_argument(
        'barcodes_handle', metavar='BARCODES', type=argparse.FileType('r'),
        help='barcodes file')
    parser_demux.add_argument(
        'input_handles', metavar='INPUT', nargs='+',
        type=argparse.FileType('r'), help='input files')
    parser_demux.add_argument(
        '-m', dest='mismatch', type=int, default=1,
        help='number of mismatches' + type_default_str)
    parser_demux.add_argument(
        '-d', dest='use_edit', action='store_true',
        help='use Levenshtein distance' + default_str)
    parser_demux.set_defaults(func=demux)

    sys.stdin = Peeker(sys.stdin)

    try:
        args = parser.parse_args()
    except IOError, error:
        parser.error(error)

    try:
        args.func(**{k: v for k, v in vars(args).items()
            if k not in ('func', 'subcommand')})
    except ValueError, error:
        parser.error(error)


if __name__ == '__main__':
    main()
