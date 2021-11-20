# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring # TODO
import os
import sys
import json
import pathlib
from contextlib import contextmanager
from typing import Any, Dict, Union, TextIO, Iterator, cast

PathLike = Union[str, bytes, 'os.PathLike[Any]']
JsonLike = Union[Any, PathLike, None]

DISPLAY_ERRORS = True  # The only mutating global.
NAME_KEY = 'name'


def print_err(message: str) -> None:
    if DISPLAY_ERRORS:
        print(f"!!!| RunMany Error: {message} |!!!", file=sys.stderr)


def set_show_errors(show_errors: bool) -> None:
    global DISPLAY_ERRORS  # pylint: disable=global-statement
    DISPLAY_ERRORS = show_errors


def load_default_settings() -> Dict[str, Any]:
    """Loads the default settings dict from default_settings.json, which is guaranteed to exist."""
    with open(pathlib.Path(__file__).with_name('default_settings.json'), encoding='utf-8') as defaults:
        return cast(Dict[str, Any], json.load(defaults))


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
