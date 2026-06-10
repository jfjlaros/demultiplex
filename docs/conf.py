from demultiplex import _author, _copyright, _project, _version


project = _project
release = _version
author = _author
copyright = _copyright

extensions = [
    'sphinx.ext.autodoc',
    'sphinx_autodoc_typehints',
    'sphinx_autodoc_argparse']
html_theme = 'sphinx_rtd_theme'
