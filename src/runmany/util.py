"""RunMany utility module."""

import os
import sys
from contextlib import contextmanager
from typing import Any, Union, TextIO, Iterator, Optional

PathLike = Union[str, bytes, 'os.PathLike[Any]']
JsonLike = Union[Any, PathLike, None]

DISPLAY_ERRORS = True  # The only mutating global.


def print_err(message: str) -> None:
    if DISPLAY_ERRORS:
        print(f"%%% RunMany Error: {message} %%%", file=sys.stderr)


def set_show_errors(show_errors: bool) -> None:
    global DISPLAY_ERRORS  # pylint: disable=global-statement
    DISPLAY_ERRORS = show_errors


def convert_smart_yes_no(val: Union[None, bool, str]) -> Optional[bool]:
    if not isinstance(val, str):
        return val
    return {'smart': None, 'yes': True, 'no': False}.get(val.lower())


@contextmanager
def nullcontext(file: TextIO) -> Iterator[TextIO]:
    """Takes the place of contextlib.nullcontext which is not present in Python 3.6."""
    yield file


def debugging() -> bool:
    return os.environ.get('DEBUG_RUNMANY') == 'True'  # pragma: no cover
