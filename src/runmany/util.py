# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring # TODO
import os
import sys
from contextlib import contextmanager
from typing import Any, Union, TextIO, Iterator

PathLike = Union[str, bytes, 'os.PathLike[Any]']
JsonLike = Union[Any, PathLike, None]

DISPLAY_ERRORS = True  # The only mutating global.
DEFAULT_SETTINGS_JSON = 'default_settings.json'
NAME_KEY = 'name'


def print_err(message: str) -> None:
    if DISPLAY_ERRORS:
        print(f"!!!| RunMany Error: {message} |!!!", file=sys.stderr)


def set_show_errors(show_errors: bool) -> None:
    global DISPLAY_ERRORS  # pylint: disable=global-statement
    DISPLAY_ERRORS = show_errors


@contextmanager
def nullcontext(file: TextIO) -> Iterator[TextIO]:
    """Takes the place of contextlib.nullcontext which is not present in Python 3.6."""
    yield file


def debugging() -> bool:
    return os.environ.get('DEBUG_RUNMANY') == 'True'  # pragma: no cover


# In 3.9 removeprefix/suffix are built in string methods.
def removeprefix(string: str, prefix: str) -> str:
    return string[len(prefix):] if string.startswith(prefix) else string


# def removesuffix(string: str, suffix: str) -> str:
#    return string[:-len(suffix)] if string.endswith(suffix) else string
