"""The core code of the Python 3 run-many package: https://pypi.org/project/run-many/"""

import os
import io
import sys
import json
import enum
import time
import types
import pathlib
import argparse
import subprocess
from collections import defaultdict
from contextlib import contextmanager, redirect_stdout
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Any, List, Dict, DefaultDict, Tuple, Union, Optional, TextIO, Iterator, cast

display_errors = True  # The only mutating global.

PathLike = Union[str, bytes, 'os.PathLike[Any]']
JsonLike = Union[None, str, bytes, 'os.PathLike[Any]', Any]

DEBUG_ENV_VAR = 'DEBUG_RUNMANY'
CODE_START, ARGV_START, STDIN_START = '~~~|', '@@@|', '$$$|'
CODE_END, ARGV_END, STDIN_END = '|~~~', '|@@@', '|$$$'
CODE_SEP, ARGV_SEP, STDIN_SEP = '~~~|~~~', '@@@|@@@', '$$$|$$$'
COMMENT_START, COMMENT_END, EXIT_SEP = '%%%|', '|%%%', '%%%|%%%'
LANGUAGE_DIVIDER, COMMENT_PREFIX = '|', '!'

OUTPUT_FILL, OUTPUT_FILL_WIDTH = '-', 60
OUTPUT_DIVIDER = OUTPUT_FILL * int(1.5 * OUTPUT_FILL_WIDTH)

DEFAULT_SETTINGS_JSON_FILE = 'default_settings.json'
ALL_NAME_KEY, NAME_KEY, COMMAND_KEY, EXT_KEY = 'all_name', 'name', 'command', 'ext'
STDERR_NZEC, STDERR_NEVER = ('nzec', None), ('never', False)


class Placeholders:
    prefix = '$'
    ARGV = 'argv'
    # For file .../dir/file.ext the parts are:
    RAWDIR = 'rawdir'        # .../dir
    DIR = 'dir'              # ".../dir"
    RAWFILE = 'rawfile'      # .../dir/file.ext
    FILE = 'file'            # ".../dir/file.ext"
    RAWBRANCH = 'rawbranch'  # .../dir/file
    BRANCH = 'branch'        # ".../dir/file"
    NAME = 'name'            # file.ext
    STEM = 'stem'            # file
    EXT = 'ext'              # .ext
    SEP = 'sep'              # /


def debugging() -> bool:
    return os.environ.get(DEBUG_ENV_VAR) == 'True'  # pragma: no cover


@contextmanager
def nullcontext(file: TextIO) -> Iterator[TextIO]:
    """Takes the place of contextlib.nullcontext which is not present in Python 3.6."""
    yield file


def print_err(message: str) -> None:
    if display_errors:
        print(f"***| RunMany Error: {message} |***", file=sys.stderr)


def removeprefix(string: str, prefix: str) -> str:
    return string[len(prefix):] if string.startswith(prefix) else string


def removesuffix(string: str, suffix: str) -> str:
    return string[:-len(suffix)] if string.endswith(suffix) else string


class LanguageData:
    def __init__(self, language_obj: Any, parent: 'Settings') -> None:
        self.obj = language_obj
        self.default_obj = None
        self.parent = parent

    def update_obj(self, language_obj: Any) -> None:
        self.obj, self.default_obj = language_obj, self.obj

    def __getattr__(self, name: str) -> Any:
        if hasattr(self.obj, name):
            return getattr(self.obj, name)
        if hasattr(self.default_obj, name):
            return getattr(self.default_obj, name)
        return getattr(self.parent, name)


class Settings:
    @staticmethod
    def normalize(language: str) -> str:
        return language.strip().lower()

    @staticmethod
    def json_to_class(json_string: str) -> Any:
        return json.loads(json_string, object_hook=lambda d: types.SimpleNamespace(**d))

    @staticmethod
    def get_json_string(settings_json: JsonLike) -> str:
        if settings_json is None:
            return str({})
        elif isinstance(settings_json, dict):  # Assume already valid json dict.
            return json.dumps(settings_json)
        with open(settings_json) as file:  # Assume path like.
            return file.read() or str({})

    def language_obj_valid(self, language_obj: Any, is_default: bool) -> bool:
        end = ". Ignoring language."

        if not hasattr(language_obj, NAME_KEY):
            print_err(f'No "{NAME_KEY}" key found for json list item{end}')
            return False

        if Settings.normalize(language_obj.name) == Settings.normalize(self.all_name):
            print_err(f'Language name "{language_obj.name}" cannot match {ALL_NAME_KEY} "{self.all_name}"{end}')
            return False

        default_obj = self[language_obj.name] if not is_default and language_obj.name in self else None
        if not hasattr(language_obj, COMMAND_KEY) and not hasattr(default_obj, COMMAND_KEY):
            print_err(f'No "{COMMAND_KEY}" key found for {language_obj.name}{end}')
            return False

        return True

    def __init__(self, settings_json: JsonLike) -> None:
        self.data = self.json_to_class(self.get_json_string(settings_json))
        with open(pathlib.Path(__file__).with_name(DEFAULT_SETTINGS_JSON_FILE)) as file:
            self.default_data = self.json_to_class(file.read())
        global display_errors
        display_errors = self.show_errors

        self.dict: Dict[str, LanguageData] = {}
        for language_obj in self.default_languages:
            if self.language_obj_valid(language_obj, True):
                self[language_obj.name] = LanguageData(language_obj, self)

        for language_obj in self.languages:
            if self.language_obj_valid(language_obj, False):
                if language_obj.name in self:
                    self[language_obj.name].update_obj(language_obj)
                else:
                    self[language_obj.name] = LanguageData(language_obj, self)

    def __getattr__(self, name: str) -> Any:
        if hasattr(self.data, name):
            return getattr(self.data, name)
        return getattr(self.default_data, name)

    def __getitem__(self, language: str) -> Any:
        return self.dict[self.normalize(language)]

    def __setitem__(self, language: str, language_data: LanguageData) -> None:
        self.dict[self.normalize(language)] = language_data

    def __contains__(self, language: str) -> bool:
        return self.normalize(language) in self.dict

    def unpack(self, language: str) -> List[str]:
        language = self.normalize(language)
        if language == self.normalize(self.all_name):
            return list(self.dict.keys())
        if language in self:
            return [language]
        raise KeyError


class SectionType(enum.Enum):
    CODE = enum.auto()
    ARGV = enum.auto()
    STDIN = enum.auto()


class Section:
    @staticmethod
    def line_is_exit(line: str) -> bool:
        return line.rstrip() == EXIT_SEP

    @staticmethod
    def line_is_comment(line: str) -> bool:
        line = line.rstrip()
        return line == COMMENT_PREFIX + EXIT_SEP or line.endswith(COMMENT_END) and \
            (line.startswith(COMMENT_START) or line.startswith(COMMENT_PREFIX + COMMENT_START))

    @staticmethod
    def line_is_header(line: str) -> bool:
        line = removeprefix(line.rstrip(), COMMENT_PREFIX)
        starts = CODE_START, ARGV_START, STDIN_START
        ends = CODE_END, ARGV_END, STDIN_END
        seps = CODE_SEP, ARGV_SEP, STDIN_SEP
        return line in seps or any(line.startswith(s) and line.endswith(e) for s, e in zip(starts, ends))

    @staticmethod
    def get_type_start_end(header: str) -> Tuple[SectionType, str, str]:
        if header == ARGV_SEP or header.startswith(ARGV_START):
            return SectionType.ARGV, ARGV_START, ARGV_END
        elif header == STDIN_SEP or header.startswith(STDIN_START):
            return SectionType.STDIN, STDIN_START, STDIN_END
        else:
            return SectionType.CODE, CODE_START, CODE_END

    @staticmethod
    def strip_content(content: str, section_type: SectionType) -> str:
        if section_type is SectionType.ARGV:
            return content.strip('\r\n')  # Always strip argv.
        elif section_type is SectionType.STDIN:
            return content.strip('\r\n') + '\n'  # Always strip stdin except trailing newline.
        else:
            return content  # Never strip code.

    def __init__(self, header: str, content: str, settings: Settings, line_number: int) -> None:
        self.header = header.rstrip()
        self.type, start, end = self.get_type_start_end(self.header)
        self.commented = self.header.startswith(COMMENT_PREFIX)

        raw_header = removeprefix(self.header, COMMENT_PREFIX)
        self.is_sep = raw_header in (CODE_SEP, ARGV_SEP, STDIN_SEP)
        self.has_content = bool(content.strip('\r\n'))
        self.content = self.strip_content(content, self.type)
        self.line_number = line_number

        self.languages = []
        if not self.is_sep:
            raw_header = removesuffix(removeprefix(raw_header, start), end)
            for language in raw_header.split(LANGUAGE_DIVIDER):
                try:
                    self.languages.extend(settings.unpack(language))
                except KeyError:
                    if not self.commented:
                        print_err(f'Language "{language.strip()}" in section header at line {self.line_number}'
                                  ' not found in json. Skipping language.')


def section_iterator(file: TextIO, settings: Settings) -> Iterator[Union[str, Section]]:
    def current_section() -> Section:
        return Section(cast(str, header), ''.join(section_lines), settings, header_line_number)

    header: Optional[str] = None
    header_line_number = 0
    section_lines: List[str] = []
    for line_number, line in enumerate(file, 1):
        if Section.line_is_exit(line):
            break
        if Section.line_is_comment(line):
            continue
        if Section.line_is_header(line):
            if not header:
                yield ''.join(section_lines)  # Yield prologue. Only happens once. # TODO remove prologue stuff
            else:
                yield current_section()
            header = line
            header_line_number = line_number
            section_lines = []
        else:
            section_lines.append(line)

    if header:
        yield current_section()


class PathParts:
    # todo put this back to how it was
    def __init__(self, path: str) -> None:
        def quote(s: str) -> str:
            return f'"{s}"'
        p = pathlib.PurePath(path)
        self.parts: Dict[str, str] = {}
        self.parts[Placeholders.RAWDIR] = str(p.parent)
        self.parts[Placeholders.DIR] = quote(self.parts[Placeholders.RAWDIR])
        self.parts[Placeholders.RAWFILE] = str(p)
        self.parts[Placeholders.FILE] = quote(self.parts[Placeholders.RAWFILE])
        self.parts[Placeholders.RAWBRANCH] = str(p.with_suffix(''))
        self.parts[Placeholders.BRANCH] = quote(self.parts[Placeholders.RAWBRANCH])
        self.parts[Placeholders.NAME] = p.name
        self.parts[Placeholders.STEM] = p.stem
        self.parts[Placeholders.EXT] = p.suffix
        self.parts[Placeholders.SEP] = os.sep

    def fill_part(self, command: str, part: str, fill: str) -> str:
        return command.replace(f'{Placeholders.prefix}{part}', fill)

    def fill_command(self, command: str, argv: str) -> str:
        if Placeholders.prefix not in command:
            command += f' {self.parts[Placeholders.FILE]}'
            if argv:
                command += f' {argv}'
        else:
            for part, fill in self.parts.items():
                command = self.fill_part(command, part, fill)
            command = self.fill_part(command, Placeholders.ARGV, argv)
        return command


class Run:
    def __init__(self, code_section: Section, argv_section: Optional[Section], stdin_section: Optional[Section],
                 language_data: LanguageData) -> None:
        self.code_section = code_section
        self.argv_section = argv_section
        self.stdin_section = stdin_section
        self.language_data = language_data

    # TODO Add line numbers for output? --- output from line 25 ---
    @staticmethod
    def output_section(name: str, section: Optional[Section] = None) -> str:
        content = ''
        if section:
            name += f' at line {section.line_number + 1}'
            content = '\n' + section.content.strip('\r\n')
        return f'{f" {name} ":{OUTPUT_FILL}^{OUTPUT_FILL_WIDTH}}{content}\n'

    def output(self, time_taken: float, command: str, stdout: str, exit_code: Union[int, str], run_number: int) -> str:
        parts = []

        header = f'{run_number}. {self.language_data.name}'
        if self.language_data.show_time:
            header += f' ({time_taken:.2f}s)'
        if exit_code != 0:
            header += f' [exit code {exit_code}]'
        if self.language_data.show_command:
            header += f' > {command}'
        parts.append(header + '\n')

        if self.language_data.show_code:
            parts.append(self.output_section('code', self.code_section))
        if self.argv_section and self.argv_section.has_content and self.language_data.show_argv:
            parts.append(self.output_section('argv', self.argv_section))
        if self.stdin_section and self.stdin_section.has_content and self.language_data.show_stdin:
            parts.append(self.output_section('stdin', self.stdin_section))
        if self.language_data.show_output:
            parts.append(self.output_section('output'))
            parts.append(stdout)
        parts.append('\n')  # TODO Have compact option that does not add this newline? or spacing = 0+ option

        return ''.join(parts)

    def get_stderr(self) -> int:
        if self.language_data.stderr in STDERR_NZEC:
            return subprocess.PIPE
        elif self.language_data.stderr in STDERR_NEVER:
            return subprocess.DEVNULL
        else:
            return subprocess.STDOUT

    def run(self, directory: str, run_number: int) -> Tuple[str, str, bool]:
        with NamedTemporaryFile(mode='w', suffix=self.language_data.ext, dir=directory, delete=False) as code_file:
            code_file.write(self.code_section.content)
            code_file_name = code_file.name

        argv = self.argv_section.content if self.argv_section and self.argv_section.has_content else ''
        stdin = self.stdin_section.content if self.stdin_section and self.stdin_section.has_content else None
        command = PathParts(code_file_name).fill_command(cast(str, self.language_data.command), argv)

        start_time = time.perf_counter()
        try:
            # Using universal_newlines=True instead of text=True here for backwards compatability with Python 3.6.
            result = subprocess.run(command, input=stdin, timeout=self.language_data.timeout, shell=True,
                                    universal_newlines=True, stdout=subprocess.PIPE, stderr=self.get_stderr())
            time_taken = time.perf_counter() - start_time
        except subprocess.TimeoutExpired:
            time_taken = time.perf_counter() - start_time
            stdout = f'TIMED OUT OF {self.language_data.timeout:g}s LIMIT'
            exit_code: Union[int, str] = 'T'
        else:
            stdout = result.stdout
            exit_code = result.returncode
            if exit_code != 0 and self.language_data.stderr in STDERR_NZEC:
                stdout += result.stderr

        output = self.output(time_taken, command, stdout, exit_code, run_number)
        return output, stdout, exit_code == 0


def prologue(content: str) -> str:
    content = content.strip()
    if content:
        content = '\n' + content
    return f'{OUTPUT_DIVIDER}\nRunMany Result{content}\n{OUTPUT_DIVIDER}\n\n'


def epilogue(total_runs: int, successful_runs: int, equal_stdouts: Optional[DefaultDict[str, List[int]]]) -> str:
    line1 = f'{successful_runs}/{total_runs} program{"" if total_runs == 1 else "s"} successfully run'
    if successful_runs < total_runs:
        line1 += f'. {total_runs - successful_runs} failed due to non-zero exit code or timeout.'
    else:
        line1 += '!'

    line2 = ''
    if equal_stdouts is not None:
        groups = sorted(equal_stdouts.values(), key=len)
        biggest = len(groups[-1]) if groups else 0
        line2 = f'\n{biggest}/{total_runs} had the exact same stdout'
        if biggest != total_runs:
            line2 += '. Equal runs grouped: ' + ' '.join('[' + ' '.join(map(str, group)) + ']' for group in groups)
        else:
            line2 += '!'

    return f'{OUTPUT_DIVIDER}\n{line1}{line2}\n{OUTPUT_DIVIDER}'


def run_iterator(file: TextIO, settings: Settings) -> Iterator[Union[str, Run]]:
    lead_section: Optional[Section] = None
    argvs: DefaultDict[str, List[Optional[Section]]] = defaultdict(lambda: [None])
    stdins: DefaultDict[str, List[Optional[Section]]] = defaultdict(lambda: [None])

    for section in section_iterator(file, settings):
        if isinstance(section, str):
            yield section  # Yield prologue. Only happens once.
            continue

        if section.commented:
            continue

        if section.is_sep:
            if not lead_section or section.type is not lead_section.type:
                print_err(
                    f'No matching lead section for "{section.header}" on line {section.line_number}. Skipping section.')
                continue
        else:
            lead_section = section

        if section.type is SectionType.ARGV:
            for language in lead_section.languages:
                if not section.is_sep:
                    argvs[language].clear()
                argvs[language].append(section)

        elif section.type is SectionType.STDIN:
            for language in lead_section.languages:
                if not section.is_sep:
                    stdins[language].clear()
                stdins[language].append(section)

        elif section.type is SectionType.CODE:
            for language in lead_section.languages:
                for argv_section in argvs[language]:
                    for stdin_section in stdins[language]:
                        yield Run(section, argv_section, stdin_section, settings[language])

# todo split up into files - runmanys and main, run, section, settings, constants


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
        settings = Settings(settings_json)
        total_runs, successful_runs = 0, 0
        equal_stdouts: DefaultDict[str, List[int]] = defaultdict(list)

        context_manager = io.StringIO(cast(str, many_file)) if from_string else open(many_file)
        with context_manager as manyfile, TemporaryDirectory() as directory:
            for run in run_iterator(manyfile, settings):
                if isinstance(run, str):
                    if settings.show_prologue:
                        print(prologue(run))
                else:
                    run_number = total_runs + 1
                    output, stdout, success = run.run(directory, run_number)
                    total_runs += 1
                    successful_runs += success
                    if settings.show_runs:
                        print(output)
                    if settings.check_equal:
                        equal_stdouts[stdout].append(run_number)
            if settings.show_epilogue:
                print(epilogue(total_runs, successful_runs, equal_stdouts if settings.check_equal else None))


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
    """The command line parser for run_many. Normally called via "runmany <argv>" from terminal. \
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
        example = 'argv'
        runmany(pathlib.Path(__file__).parent.parent.parent.joinpath('examples').joinpath(f'{example}.many'))
