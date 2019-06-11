from collections import defaultdict
from os.path import basename, splitext

from Bio import SeqIO
from dict_trie import Trie
from fastools import guess_file_format, guess_header_format
from jit_open import Handle, Queue


_get_barcode = {
    'normal' : lambda record: record.id.split('#')[1].split('/')[0],
    'x': lambda record: record.description.split(':')[-1],
    'unknown': lambda record: str(record.seq)}


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
    filenames = list(map(lambda x: x.name, input_handles))
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
    readers = list(map(
        lambda x: SeqIO.parse(x, file_format), input_handles))

    while True:
        records = list(map(lambda x: next(x), readers))
        if not records:
            break

        barcode = distance_function(extractor.get(records[0]), mismatch)
        if barcode:
            _write(barcodes[barcode], records, file_format)
        else:
            _write(default_handles, records, file_format)

    queue.flush()
