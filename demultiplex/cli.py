import argparse
import sys

from fastools import Peeker

from . import doc_split, usage, version
from .demultiplex import Extractor, count, demultiplex


def guess(
        input_handle, output_handle, in_read, start, end,
        sample_size, threshold, use_freq):
    """Retrieve the most frequent barcodes."""
    extractor = Extractor(input_handle, in_read, start, end)
    barcodes = count(input_handle, extractor, sample_size, threshold, use_freq)

    for i, barcode in enumerate(sorted(barcodes)):
        output_handle.write('{} {}\n'.format(i + 1, barcode))


def demux(
        input_handles, barcodes_handle, in_read, start, end, mismatch,
        use_edit):
    """Demultiplex any number of files given a list of barcodes."""
    extractor = Extractor(input_handles[0], in_read, start, end)
    demultiplex(input_handles, barcodes_handle, extractor, mismatch, use_edit)


def main():
    """Main entry point."""
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

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=usage[0], epilog=usage[1])
    parser.add_argument('-v', action='version', version=version(parser.prog))
    subparsers = parser.add_subparsers(dest='subcommand')
    subparsers.required = True

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
    except IOError as error:
        parser.error(error)

    try:
        args.func(**{k: v for k, v in vars(args).items()
            if k not in ('func', 'subcommand')})
    except ValueError as error:
        parser.error(error)


if __name__ == '__main__':
    main()
