from argparse import ArgumentParser, RawDescriptionHelpFormatter
from bz2 import open as bz2_open
from collections import defaultdict
from gzip import open as gzip_open
from sys import stdin, stdout

from fastools import Peeker

from . import doc_split, usage, version
from .demultiplex import _get_barcode, Extractor, count, demultiplex, match

_type_handler = defaultdict(lambda: open, {
    'bz2': bz2_open,
    'bzip2': bz2_open,
    'gz': gzip_open,
    'gzip': gzip_open})


def _file_type(*args, **kwargs):
    """Argparse FileType replacement."""
    def _open(name):
        return _type_handler[name.split('.')[-1]](name, *args, **kwargs)

    return _open


def guess(
        input_handle, output_handle, in_read, fmt, start, end, sample_size,
        threshold, use_freq):
    """Retrieve the most frequent barcodes."""
    extractor = Extractor(input_handle, in_read, fmt, start, end)
    barcodes = count(input_handle, extractor, sample_size, threshold, use_freq)

    for i, barcode in enumerate(sorted(barcodes)):
        output_handle.write('{} {}\n'.format(i + 1, barcode))


def demux(
        input_handles, barcodes_handle, in_read, fmt, start, end, mismatch,
        use_edit, path='.'):
    """Demultiplex any number of files given a list of barcodes."""
    extractor = Extractor(input_handles[0], in_read, fmt, start, end)
    demultiplex(
        input_handles, barcodes_handle, extractor, mismatch, use_edit, path)


def bcmatch(input_handle, barcodes_handle, mismatch, use_edit, path='.'):
    """Demultiplex one file given a list of barcode tuples."""
    match(input_handle, barcodes_handle, mismatch, use_edit, path)


def main():
    """Main entry point."""
    default_str = ' (default: %(default)s)'
    type_default_str = ' (%(type)s default: %(default)s)'
    type_default_str_str = ' (%(type)s default: "%(default)s")'

    common_parser = ArgumentParser(add_help=False)
    common_parser.add_argument(
        '-r', dest='in_read', action='store_true',
        help='extract the barcodes from the read' + default_str)
    common_parser.add_argument(
        '--format', dest='fmt', default=None, choices=_get_barcode.keys(),
        help='provdide the header format' + default_str)
    common_parser.add_argument(
        '-s', dest='start', type=int, default=None,
        help='start of the selection' + type_default_str)
    common_parser.add_argument(
        '-e', dest='end', type=int, default=None,
        help='end of the selection' + type_default_str)

    common_options_parser = ArgumentParser(add_help=False)
    common_options_parser.add_argument(
        '-m', dest='mismatch', type=int, default=1,
        help='number of mismatches' + type_default_str)
    common_options_parser.add_argument(
        '-d', dest='use_edit', action='store_true',
        help='use Levenshtein distance' + default_str)
    common_options_parser.add_argument(
        '-p', dest='path', type=str, default='.',
        help='output directory' + type_default_str_str)

    parser = ArgumentParser(
        formatter_class=RawDescriptionHelpFormatter,
        description=usage[0], epilog=usage[1])
    parser.add_argument('-v', action='version', version=version(parser.prog))
    subparsers = parser.add_subparsers(dest='subcommand')
    subparsers.required = True

    subparser = subparsers.add_parser(
        'guess', parents=[common_parser], description=doc_split(guess))
    subparser.add_argument(
        'input_handle', metavar='INPUT', type=_file_type('rt'),
        help='input file')
    subparser.add_argument(
        '-o', dest='output_handle', metavar='OUTPUT',
        type=_file_type('wt'), default=stdout,
        help='output file (default: <stdout>)')
    subparser.add_argument(
        '-n', dest='sample_size', type=int, default=1000000,
        help='sample size' + type_default_str)
    subparser.add_argument(
        '-f', dest='use_freq', action='store_true',
        help='select on frequency instead of a fixed amount' + default_str)
    subparser.add_argument(
        '-t', dest='threshold', type=int, default=12,
        help='threshold for the selection method' + type_default_str)
    subparser.set_defaults(func=guess)

    subparser = subparsers.add_parser(
        'demux', parents=[common_parser, common_options_parser],
        description=doc_split(demux))
    subparser.add_argument(
        'barcodes_handle', metavar='BARCODES', type=_file_type('rt'),
        help='barcodes file')
    subparser.add_argument(
        'input_handles', metavar='INPUT', nargs='+', type=_file_type('rt'),
        help='input files')
    subparser.set_defaults(func=demux)

    subparser = subparsers.add_parser(
        'match', parents=[common_options_parser],
        description=doc_split(bcmatch))
    subparser.add_argument(
        'barcodes_handle', metavar='BARCODES', type=_file_type('rt'),
        help='barcodes file')
    subparser.add_argument(
        'input_handle', metavar='INPUT', type=_file_type('rt'),
        help='input file')
    subparser.set_defaults(func=bcmatch)

    global stdin
    stdin = Peeker(stdin)

    try:
        args = parser.parse_args()
    except IOError as error:
        parser.error(error)

    try:
        args.func(
            **{k: v for k, v in vars(args).items()
                if k not in ('func', 'subcommand')})
    except (ValueError, OSError) as error:
        parser.error(error)


if __name__ == '__main__':
    main()
