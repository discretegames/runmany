"""The runmany interface module. Contains exported functions and command line handling."""

import io
import sys
import json
import pathlib
import argparse
from contextlib import redirect_stdout
from typing import List, Union, Optional, TextIO, cast

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))  # Dumb hack so project can be tested locally.

from runmany.util import PathLike, JsonLike, nullcontext, debugging, print_err  # noqa # pylint: disable=wrong-import-position
from runmany.runner import run  # noqa # pylint: disable=wrong-import-position
from runmany.newsettings import NewSettings  # noqa # pylint: disable=wrong-import-position


def load_manyfile(manyfile: Union[PathLike, str], from_string: bool) -> str:
    """Loads a manyfile from a string or file, returning it as a string."""
    if from_string:
        return cast(str, manyfile)
    with open(manyfile, encoding='utf-8') as file:
        return file.read()

# TODO maybe move this to place where it can load embedded jsons, either dict or string path, or raw path


def load_settings(settings: JsonLike) -> NewSettings:
    """Loads the settings JSON into a settings object, using default updatable settings if none provided."""
    if settings is None:
        settings_dict = {}
    elif isinstance(settings, dict):
        settings_dict = settings
    else:
        try:
            with open(settings, encoding='utf-8') as file:
                settings_dict = json.load(file)
        except Exception as error:  # pylint: disable=broad-except
            print_err(f'JSON issue - {error}. Using default settings JSON.')
            settings_dict = {}
    return NewSettings(settings_dict, settings is None)


def start_run(manyfile: Union[PathLike, str], settings: JsonLike, outfile: TextIO, from_string: bool) -> None:
    """Starts the run of a .many file."""
    manyfile_string = load_manyfile(manyfile, from_string)
    settings_object = load_settings(settings)
    with redirect_stdout(outfile):
        run(manyfile_string, settings_object)


def runmany(manyfile: Union[PathLike, str], settings: JsonLike = None,
            outfile: Optional[Union[PathLike, TextIO]] = None, from_string: bool = False) -> None:
    """Runs `manyfile` with the settings from `settings` JSON, outputting the results to stdout or `outfile`.

    Args:
        - `manyfile` (PathLike | str): The file path to or the string contents of the .many file to run.
        - `settings` (optional JsonLike): The file path to or the loaded dict of the settings JSON to use.
          Undefined settings default to their values in [default_settings.json](https://git.io/J16Z1).
          When `None`, all default settings are used. Defaults to `None`
        - `outfile` (optional PathLike | TextIO | None): The file path to or the opened file object of the file to send
          output to, or `None` to send output to stdout. Defaults to `None`.
        - `from_string` (optional bool): When `True`, `manyfile` is read as a string rather than a file path.
          Defaults to `False`.

    Returns: `None`
    """
    def opener() -> TextIO:
        if outfile is None:
            return cast(TextIO, nullcontext(sys.stdout))
        if isinstance(cast(TextIO, outfile), io.TextIOBase):
            return cast(TextIO, outfile)
        return open(cast(PathLike, outfile), 'w', encoding='utf-8')

    with opener() as output_file:
        start_run(manyfile, settings, output_file, from_string)


def runmanys(manyfile: Union[PathLike, str], settings: JsonLike = None, from_string: bool = False) -> str:
    """Runs `manyfile` with the settings from `settings` JSON, returning the results as a string.

    Args:
        - `manyfile` (PathLike | str): The file path to or the string contents of the .many file to run.
        - `settings` (optional JsonLike): The file path to or the loaded dict of the settings JSON to use.
          Undefined settings default to their values in [default_settings.json](https://git.io/J16Z1).
          When `None`, all default settings are used. Defaults to `None`
        - `from_string` (optional bool): When `True`, `manyfile` is read as a string rather than a file path.
          Defaults to `False`.

    Returns: (str) The results of the run that would normally appear on stdout as a string.
    """
    with io.StringIO() as output_file:
        start_run(manyfile, settings, output_file, from_string)
        output_file.seek(0)
        return output_file.read()


def cmdline(argv: List[str]) -> None:
    """The command line parser for runmany. Usually called via "runmany <argv>" in terminal but can be called from code.

    Args:
        - `argv` (List[str]): The space separated args that would normally be given on the command line.

    Returns: `None`
    """
    description = 'Runs a .many file. Full documentation: https://github.com/discretegames/runmany/blob/main/README.md'
    parser = argparse.ArgumentParser(prog='runmany', description=description)
    parser.add_argument('manyfile', metavar='<manyfile>', help='the path to the .many file to run')
    parser.add_argument('-s', '--settings', metavar='<settings>',
                        help='the path to the .json settings file to use which overrides any embedded settings')
    parser.add_argument('-o', '--outfile', metavar='<outfile>', help='the path to the file output is redirected to')
    args = parser.parse_args(argv)
    runmany(args.manyfile, args.settings, args.outfile)


def main() -> None:
    """Function that is called when runmany is run from the command line or this file is run directly."""
    cmdline(sys.argv[1:])  # pragma: no cover


if __name__ == '__main__':  # pragma: no cover
    if not debugging():
        main()
    else:
        runmany(pathlib.Path(__file__).parent.parent.parent.joinpath('scratch/scratch.many'))
