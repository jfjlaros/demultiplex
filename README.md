# Fastools
This package provides various tools for the analysis and manipulation of FASTA
and FASTQ files.

## Installation
Via [pypi](https://pypi.python.org/pypi/fastools):

    pip install fastools

From source:

    git clone https://git.lumc.nl/j.f.j.laros/fastools.git
    cd fastools
    pip install .

## Command line interfaces
This package provides three separate command line interfaces, one for
*demultiplexing*, one for splitting FASTA files on substring occurrence and the
main interface that provides a large number of small conversion and
manipulation procedures.

## `fastools`
The `fastools` command line interface provides a large number of elementary
procedures that can be chained to get more complex behaviour. The elementary
procedures can be accessed as subcommands of the main program. To get the full
list of subcommands, type:

    fastools -h

To get help on a specific subcommand, e.g., `sanitise`, type:

    fastools sanitise -h

As mentioned above, more complex behaviour can be obtained by chaining
elementary command by using UNIX pipes. For example, Fastools has the
subcommand `gen` for generating a random FASTA record and the subcommand
`fa2fq` to convert a FASTA file to a FASTQ file. To combine these two
subcommands, we do the following:

    fastools gen - name description 60 | fastools fa2fq - output.fq

This produces a FASTQ file containing one random sequence. Similarly a dash
(`-`) can always be used instead of a file name to use standard input or
standard output.

### Automatic detection of input formats
Some subcommands, like `lenfilt`, accepts both FASTA and FASTQ files as input.
The output format will be set to the same type as the input format. So to use this command with FASTA files, we use:

    fastools lenfilt -l 25 input.fa small.fa large.fa

and for FASTQ, we can use:

    fastools lenfilt -l 25 input.fq small.fq large.fq

In bother cases, sequences larger than 25 are written to the `large` file, the
other sequences are written to the `small` file.

## `demultiplex`
The `demultiplex` program provides several ways to demultiplex any number of
FASTA or a FASTQ files based on a list of barcodes. This list can either be
provided via a file or guessed from the data. The demultiplexer can be set to
search for the barcodes in the header, or in the read itself. To allow for
mismatches, two distance functions (edit distance and Hamming distance) are
available.

### Illumina FASTQ files
For Illumina FASTQ files, the barcodes can usually be found in the header of
each FASTQ record. Currently, the `demultiplex` program supports two types of
headers, the classical Illumina headers and the newer HiSeq X headers. These
headers are detected automatically.

Demultiplexing is done with the `demux` subcommand by providing a list of
barcodes. The barcodes file is formatted as follows:

    name sequence

So a typical barcodes file might look like this:

    index1 ACGTAA
    index2 GTAAGG

To use this to demultiplex two FASTQ files, where we assume that the barcode
can be found in the header of the first file, we use the following command:

    demultiplex demux barcodes.csv file_1.fq file_2.fq

This will generate six files:

    file_1_index1.fq
    file_2_index1.fq
    file_1_index2.fq
    file_2_index2.fq
    file_1_UNKNOWN.fq
    file_2_UNKNOWN.fq

the first four files will contain records assigned to index1 and index2, the
last two will contain anything that could not be assigned.

If the list of barcodes is not known beforehand, the `guess` subcommand can be
used to search for a top list of barcodes. For example, if we want to search
for the top five barcodes in the first 1000 records, we use the following:

    demultiplex guess -o barcodes.csv -t 5 -n 1000 file.fq

This will generate the barcodes file that can be used for the `demux`
subcommand.

If the number of barcodes is not known beforehand, an alternative selection
method can be used which selects all barcodes with a minimum number of
occurrences. The following command will generate a barcode file of all barcodes
that occur at least five times in the first 1000 reads:

    demultiplex guess -o barcodes.csv -f -t 5 -n 1000 file.fq

### Other files
For platforms other than Illumina, or for alternative sequencing runs, like
those coming from 10X experiments, barcodes sometimes end up at a specific
location in each read. It can also be that the barcode is in the header, but
only part of this barcode is used, this happens when dual indexing is used for
example. To deal with these cases, both the `quess` as well as the `demux`
subcommand can be instructed to look voor the barcode in the read with the `-r`
option and a selection can be made by providing a start- and end coordinate
via the `-s` and `-e` options. For example, if we want to search for barcodes
in the first six nucleotides of a read, we use the following command:

    demultiplex demux -r -e 6 barcodes.csv file.fq

## `split_fasta`
The `split_fasta` program splits a FASTA file based on the occurrence of
markers. For more information, use the *help* option:

    split_fasta -h

## Library
All public functions in the `fastools` module are directly usable from other
programs. To access the library, simply import `fastools`:

```python
>>> from fastools import fastools
>>>
>>> # Make a random FASTA record and write it to `output.fa`.
>>> handle = open('output.fa', 'w')
>>> fastools.generate_dna(10, handle, 'name', 'description')
```
