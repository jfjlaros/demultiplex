from tssv import align


def multi_align(reference, barcodes, distance, indel_score):
    """Align multiple barcodes in order to a reference.

    :arg str reference:
    :arg list barcodes:
    :arg int distance:
    :arg int indel_score:

    :returns bool: True if all barcodes align in order, False otherwise.
    """
    _reference = reference

    for barcode in barcodes:
        alignment = align(_reference, barcode, indel_score)

        if alignment['distance'] > distance:
            return False

        _reference = _reference[alignment['position']:]

    return True
