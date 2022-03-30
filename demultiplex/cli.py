from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from sys import stdin

from fastools import Peeker

from . import doc_split, usage, version
from .demultiplex import (
    _get_barcode, _type_handler, Extractor, count, demultiplex, match)


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


def bcmatch(
        input_handles, barcodes_handle, mismatch, use_edit, path='.',
        filter_multiple=False, directional=False):
    """Demultiplex one file given a list of barcode tuples."""
    match(
        input_handles, barcodes_handle, mismatch, use_edit, path,
        filter_multiple, directional)


def _arg_parser() -> object:
    """Command line argument parsing."""
    common_parser = ArgumentParser(add_help=False)
    common_parser.add_argument(
        '-r', dest='in_read', action='store_true',
        help='extract the barcodes from the read')
    common_parser.add_argument(
        '--format', dest='fmt', default=None, choices=_get_barcode.keys(),
        help='provdide the header format')
    common_parser.add_argument(
        '-s', dest='start', type=int, default=None,
        help='start of the selection')
    common_parser.add_argument(
        '-e', dest='end', type=int, default=None, help='end of the selection')

    common_options_parser = ArgumentParser(add_help=False)
    common_options_parser.add_argument(
        '-m', dest='mismatch', type=int, default=1,
        help='number of mismatches')
    common_options_parser.add_argument(
        '-d', dest='use_edit', action='store_true',
        help='use Levenshtein distance')
    common_options_parser.add_argument(
        '-p', dest='path', type=str, default='.', help='output directory')

    input_parser = ArgumentParser(add_help=False)
    input_parser.add_argument(
        'barcodes_handle', metavar='BARCODES', type=_file_type('rt'),
        help='barcodes file')
    input_parser.add_argument(
        'input_handles', metavar='INPUT', nargs='+', type=_file_type('rt'),
        help='input files')

    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter, description=usage[0],
        epilog=usage[1])
    parser.add_argument('-v', action='version', version=version(parser.prog))
    subparsers = parser.add_subparsers(dest='subcommand')
    subparsers.required = True

    subparser = subparsers.add_parser(
        'guess', formatter_class=ArgumentDefaultsHelpFormatter,
        parents=[common_parser], description=doc_split(guess))
    subparser.add_argument(
        'input_handle', metavar='INPUT', type=_file_type('rt'),
        help='input file')
    subparser.add_argument(
        '-o', dest='output_handle', metavar='OUTPUT', type=_file_type('wt'),
        default='-', help='output file')
    subparser.add_argument(
        '-n', dest='sample_size', type=int, default=1000000,
        help='sample size')
    subparser.add_argument(
        '-f', dest='use_freq', action='store_true',
        help='select on frequency instead of a fixed amount')
    subparser.add_argument(
        '-t', dest='threshold', type=int, default=12,
        help='threshold for the selection method')
    subparser.set_defaults(func=guess)

    subparser = subparsers.add_parser(
        'demux', formatter_class=ArgumentDefaultsHelpFormatter,
        parents=[common_parser, common_options_parser, input_parser],
        description=doc_split(demux))
    subparser.set_defaults(func=demux)

    subparser = subparsers.add_parser(
        'match', formatter_class=ArgumentDefaultsHelpFormatter,
        parents=[common_options_parser, input_parser],
        description=doc_split(bcmatch))
    subparser.add_argument(
        '-f', dest='filter_multiple', default=False, action='store_true',
        help='write multiple matches to separate files')
    subparser.add_argument(
        '-D', dest='directional', default=False, action='store_true',
        help='directional input data')
    subparser.set_defaults(func=bcmatch)

    return parser


def main():
    """Main entry point."""
    parser = _arg_parser()

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
