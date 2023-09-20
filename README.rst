Demultiplex: FASTA/FASTQ demultiplexer
======================================

.. image:: https://img.shields.io/github/last-commit/jfjlaros/demultiplex.svg
   :target: https://github.com/jfjlaros/demultiplex/graphs/commit-activity
.. image:: https://github.com/jfjlaros/demultiplex/actions/workflows/python-package.yml/badge.svg
   :target: https://github.com/jfjlaros/demultiplex/actions/workflows/python-package.yml
.. image:: https://readthedocs.org/projects/demultiplex/badge/?version=latest
   :target: https://demultiplex.readthedocs.io/en/latest
.. image:: https://img.shields.io/github/release-date/jfjlaros/demultiplex.svg
   :target: https://github.com/jfjlaros/demultiplex/releases
.. image:: https://img.shields.io/github/release/jfjlaros/demultiplex.svg
   :target: https://github.com/jfjlaros/demultiplex/releases
.. image:: https://img.shields.io/pypi/v/demultiplex.svg
   :target: https://pypi.org/project/demultiplex/
.. image:: https://img.shields.io/github/languages/code-size/jfjlaros/demultiplex.svg
   :target: https://github.com/jfjlaros/demultiplex
.. image:: https://img.shields.io/github/languages/count/jfjlaros/demultiplex.svg
   :target: https://github.com/jfjlaros/demultiplex
.. image:: https://img.shields.io/github/languages/top/jfjlaros/demultiplex.svg
   :target: https://github.com/jfjlaros/demultiplex
.. image:: https://img.shields.io/github/license/jfjlaros/demultiplex.svg
   :target: https://raw.githubusercontent.com/jfjlaros/demultiplex/master/LICENSE.md
.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.8362959.svg
   :target: https://zenodo.org/record/8362959
----

Versatile NGS demultiplexer with the following features:

- Support for FASTA and FASTQ files.
- Support for gzip and bzip2 compressed files.
- Support for multiple reads per fragment, e.g., paired-end.
- Handles barcodes in the header and in the reads.
- Handles barcodes at *unknown* locations in reads (e.g., PacBio or Nanopore
  barcodes).
- Support for selection of part of a barcode.
- Allows for mismatches, insertions and deletions.
- Barcode guessing by frequency or fixed amount.
- Handles large numbers (over one million) of barcodes.

Please see ReadTheDocs_ for the latest documentation.


.. _ReadTheDocs: https://demultiplex.readthedocs.io/en/latest/index.html
