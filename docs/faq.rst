Frequently asked questions
==========================

Can this program work with dual barcodes / indexes?

    Yes, but not directly. Because of the large amount of dual (or more)
    indexing approaches, the user interface would become incomprehensible. This
    is why we have decided to support only the basic cases. In order to support
    an arbitrary amount of barcodes see the :ref:`multiple_barcodes` section.


Can you add support for removing barcodes after demultiplexing?

    We used to have this type of functionality (selecting parts of a read) in a
    previous version, but because of the large number of complicated barcoding
    schemas (multiple barcodes in one read, barcodes in multiple reads, etc.),
    we found that this interface was not flexible enough. Instead, we recommend
    to use a more generic tool for post processing the demultiplexed files, The
    Fastools_ ``select`` command for example.


My sequencing run was pretty bad, can / should I increase the number of allowed
mismatches?

    It depends on which barcodes were used. Most barcode sets are designed to
    allow for single nucleotide read errors. When multiple errors occur, it may
    not be possible to uniquely assign a read to a barcode. You can use the
    Barcode_ ``test`` command to see if your barcode set allows for multiple
    error correction.


I do not know which / how many barcodes were used. How can I demultiplex my
file?

    The best thing to do is to contact your sequencing provider and ask which
    barcodes were used. If this is not possible for some reason, you may want
    to use the ``guess`` subcommand described in the :ref:`illumina` section.
    If the barcodes are in the read instead of the header, you may want to use
    a tool like FastQC_ to find overrepresented sequences. These may be the
    barcodes you are looking for.

I get the message "error: invalid barcodes file format". What is wrong?

    The columns in ``barcodes.tsv`` should be separated by spaces or tabs,
    using other delimiters will result in this error message. Also note that
    the ``demux`` subcommand only allows for one barcode, while the ``match``
    command can work with multiple barcodes.


.. _FastQC: https://www.bioinformatics.babraham.ac.uk/projects/fastqc/
.. _Fastools: https://fastools.readthedocs.io/
.. _Barcode: https://barcode.readthedocs.io/
