"""demultiplex: Demultiplex any number of FASTA or a FASTQ files based on a
list of barcodes.


Format of the barcode file:
name barcode

Copyright (c) 2015 Leiden University Medical Center <humgen@lumc.nl>
Copyright (c) 2015 Jeroen F.J. Laros <J.F.J.Laros@lumc.nl>

Licensed under the MIT license, see the LICENSE file.
"""
from .demultiplex import Extractor, count, demultiplex


__version_info__ = ('0', '1', '0')

__version__ = '.'.join(__version_info__)
__author__ = 'Jeroen F.J. Laros'
__contact__ = 'J.F.J.Laros@lumc.nl'
__homepage__ = 'https://github.com/jfjlaros/demultiplex'

usage = __doc__.split('\n\n\n')


def doc_split(func):
    return func.__doc__.split('\n\n')[0]


def version(name):
    return '{} version {}\n\nAuthor   : {} <{}>\nHomepage : {}'.format(
        name, __version__, __author__, __contact__, __homepage__)
