from importlib.metadata import PackageNotFoundError, metadata
from re import split
from typing import Callable

from .demultiplex import Extractor, count, demultiplex


def _extract(key: str, delim: str = r'[^\s\S]', index: int = 0) -> str:
    try:
        value = metadata(__package__).get(key, '')
    except PackageNotFoundError:
        return '<NO DATA>'
    return split(delim, value)[index]


def doc_split(func: Callable) -> str:
    return func.__doc__.split('\n\n')[0]


_project = _extract('Name')
_version = _extract('Version')
_year = '2013-2026'
_author = _extract('Author')
_email = _extract('Author-email')
_description = _extract('Summary')
_copyright = f'Copyright (c) {_year} by {_author} <{_email}>'
_url = _extract('Project-URL')
_info = f'{_project} version {_version}\n\n{_copyright}\nHomepage: {_url}'
