import os
import sys
from contextlib import contextmanager
from typing import Any, Union, TextIO, Iterator

display_errors = True  # The only mutating global.

PathLike = Union[str, bytes, 'os.PathLike[Any]']
JsonLike = Union[None, str, bytes, 'os.PathLike[Any]', Any]


def print_err(message: str) -> None:
    if display_errors:
        print(f"!!!| RunMany Error: {message} |!!!", file=sys.stderr)


def set_show_errors(show_errors: bool) -> None:
    global display_errors
    display_errors = show_errors


@contextmanager
def nullcontext(file: TextIO) -> Iterator[TextIO]:
    """Takes the place of contextlib.nullcontext which is not present in Python 3.6."""
    yield file


def debugging() -> bool:
    return os.environ.get('DEBUG_RUNMANY') == 'True'  # pragma: no cover


def removeprefix(string: str, prefix: str) -> str:
    return string[len(prefix):] if string.startswith(prefix) else string


def removesuffix(string: str, suffix: str) -> str:
    return string[:-len(suffix)] if string.endswith(suffix) else string
