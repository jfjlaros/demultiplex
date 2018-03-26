import sys
from setuptools import setup

if sys.version_info < (2, 6):
    raise Exception('demultiplex requires Python 2.6 or higher.')

# Todo: How does this play with pip freeze requirement files?
requires = ['biopython', 'dict-trie', 'jit-open']

# Python 2.6 does not include the argparse module.
try:
    import argparse
except ImportError:
    requires.append('argparse')

import demultiplex as distmeta

setup(
    name='demultiplex',
    version=distmeta.__version__,
    description='FASTA/FASTQ analysis and manipulation toolkit.',
    long_description=distmeta.__doc__,
    author=distmeta.__author__,
    author_email=distmeta.__contact__,
    url=distmeta.__homepage__,
    license='MIT License',
    platforms=['any'],
    packages=['demultiplex'],
    install_requires=requires,
    entry_points = {
        'console_scripts': [
            'demultiplex = demultiplex.demultiplex:main'
        ]
    },
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering',
    ],
    keywords='bioinformatics'
)
