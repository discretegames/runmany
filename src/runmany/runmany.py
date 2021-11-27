"""RunMany interface module. Contains exported functions and command line handling."""

import io
import sys
import pathlib
import argparse
from contextlib import redirect_stdout
from tempfile import TemporaryDirectory
from typing import List, Union, Optional, TextIO, cast

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))  # Dumb hack so project can be tested locally.

# pylint: disable=wrong-import-position
from runmany.util import PathLike, JsonLike, nullcontext, debugging  # noqa
from runmany.settings import Settings  # noqa
from runmany.runner import Runner  # noqa
from runmany.parser import Parser  # noqa


def load_manyfile(manyfile: Union[PathLike, str], from_string: bool) -> str:
    if from_string:
        return cast(str, manyfile)
    with open(manyfile, encoding='utf-8') as file:
        return file.read()


def run(manyfile: Union[PathLike, str], settings: JsonLike, outfile: TextIO, from_string: bool) -> None:
    manyfile = load_manyfile(manyfile, from_string)
    settings = Settings.from_json(settings)
    runner = Runner(settings)
    parser = Parser(manyfile, settings, runner)
    with redirect_stdout(outfile), TemporaryDirectory() as directory:
        for section in parser:
            section.run(directory)
        runner.print_results_footer()


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
        run(manyfile, settings, output_file, from_string)


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
        run(manyfile, settings, output_file, from_string)
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
    parser.add_argument('manyfile', metavar='<input-file>', help='the path to the .many file to run')
    parser.add_argument('-s', '--settings', metavar='<settings-file>',
                        help='the path to the .json settings file to use which overrides any embedded settings')
    parser.add_argument('-o', '--outfile', metavar='<output-file>', help='the path to the file output is redirected to')
    args = parser.parse_args(argv)
    runmany(args.manyfile, args.settings, args.outfile)


def main() -> None:
    cmdline(sys.argv[1:])  # pragma: no cover


if __name__ == '__main__':  # pragma: no cover
    if not debugging():
        main()
    else:
        TESTING = 0
        if TESTING:
            try:
                # Using import dunder so pylint doesn't complain.
                __import__('pytest').main(['-vv'])
            except Exception:  # pylint: disable=broad-except
                pass
            finally:
                sys.exit()
        else:
            debug_file = pathlib.Path(__file__).parent.parent.parent.joinpath('scratch/scratch.many')
            print(f'DEBUGGING RUNMANY "{debug_file}":')
            runmany(debug_file)
