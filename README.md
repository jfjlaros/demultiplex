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
The `demultiplex` command provides several ways to demultiplex a FASTA or a
FASTQ file based on a list of barcodes. This list can either be provided via a
file or guessed from the data. The demultiplexer can be set to search for the
barcodes in the header, or in the read itself. To allow for mismatches, two
distance functions (edit distance and Hamming distance) are available.

### Illumina FASTQ files
For Illumina FASTQ files, the barcodes can usually be found in the header of
each FASTQ record. Currently, the `demultiplex` program supports two types of
headers, the classical Illumina headers and the newer HiSeq X headers. These
headers are detected automatically.

The most common way to demultiplex is by providing a list of barcodes. The
barcodes file is formatted as follows:

    name sequence

So a typical barcodes file might look like this:

    index1 ACGTAA
    index2 GTAAGG

To use this to demultiplex a FASTQ file, where we assume that the barcode can
be found in the header, we use the following command:

    demultiplex -b barcodes.csv file.fq

This will generate three files:

    file_index1.fq
    file_index2.fq
    file_UNKNOWN.fq

the first two files will contain records assigned to index1 and index2, the
last one will contain anything that could not be assigned. 

If the list of barcodes is not known beforehand, the `demultiplex` program can
be told to search for a top list of barcodes. This procedure is controlled via
the `-a` and `-s` options. For example, if we want to search for the top five
barcodes in the first 1000 records, we use the following:

    demultiplex -a 5 -s 1000 file.fq

In this case, six files will be created, the first five containing records
assigned to the top five barcodes and one file containing the unassigned
records. Since no name is provided, the files will have the barcode sequence in
their filename, e.g.,

    file_ACGTAA.fq

### Other files
For platforms other than Illumina, barcodes sometimes end up at a specific
location in each read. In this case, demultiplexing is a combination of
selecting the barcode and removing this from the actual data. This can be done
with the `-l` and `-r` options. For example, if we want to search for barcodes
in the first six nucleotides of a read and want to save positions from ten to
twenty, we use the following command:

    demultiplex -b barcodes.csv -l 1 6 -r 10 20 file.fq

By default, if the `-r` option is omitted, everything after the barcode is
selected.

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
