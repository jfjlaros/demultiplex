# Make sure the package is installed and the requirements file is known.
# https://readthedocs.org/dashboard/arduino-simple-rpc/advanced/
from demultiplex import _get_metadata


author = _get_metadata('Author')
copyright = _get_metadata('Author')
project = _get_metadata('Name')
release = _get_metadata('Version')

autoclass_content = 'both'
extensions = [
    'sphinx.ext.autodoc', 'sphinx_autodoc_typehints', 'sphinxarg.ext']
master_doc = 'index'
