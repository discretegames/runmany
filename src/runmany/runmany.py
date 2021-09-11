import io
import sys
import pathlib
import argparse
from collections import defaultdict
from contextlib import redirect_stdout
from tempfile import TemporaryDirectory
from typing import List, DefaultDict, Union, Optional, TextIO, Iterator, cast

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))  # Dumb hack so project can be tested locally.

from runmany.util import PathLike, JsonLike, nullcontext, debugging  # noqa: E402
from runmany.runner import run_iterator, make_footer, Run  # noqa: E402
from runmany.settings import load_settings  # noqa: E402


def runmany_to_f(file: TextIO, many_file: Union[PathLike, str], settings_json: JsonLike = None, *,
                 from_string: bool = False) -> None:
    """Runs `many_file` with the settings from `settings_json`, writing the results to the open file object `file`.

    Args:
        - `file` (TextIO): The opened file object to write the run results to.
        - `many_file` (PathLike | str): The path to or the string contents of the .many file to run.
        - `settings_json` (optional JsonLike): The path to or the loaded json dict of the settings to use. \
Undefined settings fallback to [default_settings.json](https://git.io/JEEkL).
        - `from_string` (optional bool): When True, `many_file` is read as a string rather than a path. \
Defaults to False.
    """
    with redirect_stdout(file):
        total_runs, successful_runs = 0, 0
        equal_stdouts: DefaultDict[str, List[int]] = defaultdict(list)

        context_manager = io.StringIO(cast(str, many_file)) if from_string else open(many_file)
        with context_manager as manyfile, TemporaryDirectory() as directory:
            iterator = run_iterator(manyfile)
            settings = load_settings(settings_json, cast(str, next(iterator)))
            iterator.send(settings)

            for run in cast(Iterator[Run], iterator):
                run_number = total_runs + 1
                output, stdout, success = run.run(directory, run_number)
                total_runs += 1
                successful_runs += success
                if settings.show_runs:
                    print(output, flush=True)
                if settings.show_equal:
                    equal_stdouts[stdout].append(run_number)
            print(make_footer(settings, total_runs, successful_runs, equal_stdouts), flush=True)


def runmany_to_s(many_file: Union[PathLike, str], settings_json: JsonLike = None, *, from_string: bool = False) -> str:
    """Runs `many_file` with the settings from `settings_json`, returning the results as a string.

    Args:
        - `many_file` (PathLike | str): The path to or the string contents of the .many file to run.
        - `settings_json` (optional JsonLike): The path to or the loaded json dict of the settings to use. \
Undefined settings fallback to [default_settings.json](https://git.io/JEEkL).
        - `from_string` (optional bool): When True, `many_file` is read as a string rather than a path. \
Defaults to False.

    Returns:
        str: The results of the run that would normally appear on stdout.
    """
    with io.StringIO() as file:
        runmany_to_f(file, many_file, settings_json, from_string=from_string)
        file.seek(0)
        return file.read()


def runmany(many_file: Union[PathLike, str], settings_json: JsonLike = None, output_file: Optional[PathLike] = None, *,
            from_string: bool = False) -> None:
    """Runs `many_file` with the settings from `settings_json`, outputting the results to `output_file` or stdout.

    Args:
        - `many_file` (PathLike | str): The path to or the string contents of the .many file to run.
        - `settings_json` (optional JsonLike): The path to or the loaded json dict of the settings to use. \
Undefined settings fallback to [default_settings.json](https://git.io/JEEkL).
        - `output_file` (optional None | PathLike): The path to the file to send output to, or None for stdout. \
Defaults to None.
        - `from_string` (optional bool): When True, `many_file` is read as a string rather than a path. \
Defaults to False.
    """
    with cast(TextIO, nullcontext(sys.stdout)) if output_file is None else open(output_file, 'w') as file:
        runmany_to_f(file, many_file, settings_json, from_string=from_string)


def cmdline(argv: List[str]) -> None:
    """The command line parser for runmany. Normally called via "runmany <argv>" from terminal. \
Can alternatively be called from code.

    Args:
        - `argv` (List[str]): The space separated args that would normally be given on the command line.
    """
    parser = argparse.ArgumentParser(prog='runmany', description='Runs a .many file.')
    parser.add_argument('input', help='the .many file to run', metavar='<input-file>')
    parser.add_argument('-j', '--json', help='the .json settings file to use', metavar='<settings-file>')
    parser.add_argument('-o', '--output', help='the file output is redirected to', metavar='<output-file>')
    args = parser.parse_args(argv)
    runmany(args.input, args.json, args.output)


def main() -> None:
    cmdline(sys.argv[1:])  # pragma: no cover


if __name__ == '__main__':  # pragma: no cover
    if not debugging():
        main()
    else:
        runmany(pathlib.Path(__file__).parent.parent.parent.joinpath('_scratch/scratch.many'))
