from bz2 import open as bz2_open
from collections import defaultdict
from gzip import open as gzip_open
from os import mkdir
from os.path import basename, exists

from Bio import SeqIO
from Bio.Seq import reverse_complement
from dict_trie import Trie
from fastools import guess_file_format, guess_header_format
from jit_open import Handle, Queue

from .match import multi_align


_get_barcode = {
    'normal': lambda record: record.id.split('#')[1].split('/')[0],
    'x': lambda record: record.description.split(':')[-1],
    'umi': lambda record: record.description.split(' ')[0].split(':')[-1],
    'unknown': lambda record: str(record.seq)}

_type_handler = defaultdict(lambda: open, {
    'bz2': bz2_open,
    'bzip2': bz2_open,
    'gz': gzip_open,
    'gzip': gzip_open})


def _name(handle):
    if hasattr(handle.buffer, '_fp'):
        return handle.buffer._fp.name
    return handle.name


class Extractor(object):
    def __init__(self, handle, in_read=False, fmt=None, start=None, end=None):
        """Configure a barcode extractor.

        :arg stream handle: Handle to an NGS data file.
        :arg bool in_read: Inspect the read instead of the header.
        :arg str fmt: Header format.
        :arg int start: Start of the barcode.
        :arg int end: End of the barcode.
        """
        self._start = start
        self._end = end

        if self._start:
            self._start -= 1

        if not fmt:
            if not in_read:
                self._get_barcode = _get_barcode[guess_header_format(handle)]
            else:
                self._get_barcode = _get_barcode['unknown']
        else:
            self._get_barcode = _get_barcode[fmt]

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


def _open_files(path, filenames, barcode, queue):
    """For a list of input files, open the corresponding output files.

    :arg str path: Output directory.
    :arg list filename: List of input filenames.
    :arg str barcode: Name of the barcode.
    :arg Queue queue: Queue for open files.

    :returns list: List of handles of output files.
    """
    if not exists(path):
        mkdir(path)

    handles = []

    for filename in filenames:
        base, ext = basename(filename).split('.', True)
        handles.append(
            Handle('{}/{}_{}.{}'.format(path, base, barcode, ext), queue,
                   f_open=_type_handler[ext.split('.')[-1]]))

    return handles


def _write(handles, records, file_format):
    for i, record in enumerate(records):
        SeqIO.write(record, handles[i], file_format)


def demultiplex(
        input_handles, barcodes_handle, extractor, mismatch, use_edit,
        path='.'):
    """Demultiplex a list of NGS data files.

    :arg list input_handles: List of handles to NGS data files.
    :arg stream barcodes_handle: Handle to a file containing barcodes.
    :arg Extractor extractor: A barcode extractor.
    :arg int mismatch: Number of allowed mismatches.
    :arg bool use_edit: Use Levenshtein distance instead of Hamming distance.
    :arg str path: Output directory.
    """
    filenames = list(map(lambda x: _name(x), input_handles))
    queue = Queue()
    default_handles = _open_files(path, filenames, 'UNKNOWN', queue)

    barcodes = {}
    for line in barcodes_handle.readlines():
        try:
            name, barcode = line.strip().split()
        except ValueError:
            raise ValueError('invalid barcodes file format')
        barcodes[barcode] = _open_files(path, filenames, name, queue)

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


def match(
        input_handles, barcodes_handle, mismatch, use_edit, path='.',
        filter_multiple=False, directional=False):
    """Demultiplex a list of NGS data files.

    :arg list input_handles: List of handles to NGS data files.
    :arg stream barcodes_handle: Handle to a file containing barcodes.
    :arg int mismatch: Number of allowed mismatches.
    :arg bool use_edit: Use Levenshtein distance instead of Hamming distance.
    :arg str path: Output directory.
    :arg bool filter_multiple: Write multiple matches to separate files.
    :arg bool directional: Directional input data.
    """
    filenames = list(map(lambda x: _name(x), input_handles))
    queue = Queue()
    default_handles = _open_files(path, filenames, 'UNKNOWN', queue)
    multiple_handles = _open_files(path, filenames, 'MULTIPLE', queue)

    indel_score = 1
    if not use_edit:
        indel_score = 1000

    barcodes = []
    for line in map(lambda x: x.strip().split(), barcodes_handle.readlines()):
        try:
            name = line.pop(0)
        except (IndexError, ValueError):
            raise ValueError('invalid barcodes file format')
        barcodes.append((_open_files(path, filenames, name, queue), line))

    file_format = guess_file_format(input_handles[0])
    readers = list(map(
        lambda x: SeqIO.parse(x, file_format), input_handles))

    while True:
        records = list(map(lambda x: next(x), readers))
        if not records:
            break

        reference = str(records[0].seq)
        if directional:
            reference_rc = reverse_complement(reference)

        found_handles = []
        for handles, barcode in barcodes:
            if multi_align(reference, barcode, mismatch, indel_score):
                found_handles.append(handles)
            elif directional and multi_align(
                    reference_rc, barcode, mismatch, indel_score):
                found_handles.append(handles)

        if found_handles:
            if not filter_multiple or len(found_handles) == 1:
                for handles in found_handles:
                    _write(handles, records, file_format)
            else:
                _write(multiple_handles, records, file_format)
        else:
            _write(default_handles, records, file_format)

    queue.flush()
