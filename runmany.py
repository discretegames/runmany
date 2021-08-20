import os
import io
import sys
import abc
import json
import enum
import types
import pathlib
import argparse
import itertools
import subprocess
from collections import defaultdict
from contextlib import nullcontext, redirect_stdout
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Any, List, Dict, DefaultDict, Tuple, Union, Optional, TextIO, Iterator, cast

display_errors = True  # The only mutating global.

PathLike = Union[str, bytes, 'os.PathLike[Any]']
JsonLike = Union[None, str, bytes, 'os.PathLike[Any]', Any]

CODE_START, ARGV_START, STDIN_START = '~~~|', '@@@|', '$$$|'
CODE_END, ARGV_END, STDIN_END = '|~~~', '|@@@', '|$$$'
CODE_SEP, ARGV_SEP, STDIN_SEP = '~~~|~~~', '@@@|@@@', '$$$|$$$'
COMMENT_START, COMMENT_END, EXIT_SEP = '!!!|', '|!!!', '%%%|%%%'
LANGUAGE_DIVIDER, COMMENT_PREFIX = '|', '!'

OUTPUT_FILL, OUTPUT_FILL_WIDTH = '-', 60
OUTPUT_DIVIDER = OUTPUT_FILL * int(1.5 * OUTPUT_FILL_WIDTH)

DEFAULT_LANGUAGES_JSON_FILE = 'default_languages.json'
ALL_NAME_KEY, NAME_KEY, COMMAND_KEY, EXT_KEY = 'all_name', 'name', 'command', 'ext'
STDERR_NZEC, STDERR_NEVER = ('nzec', None), ('never', False)


class Placeholders(abc.ABC):
    prefix = '$'
    ARGV = '$argv'
    # For file .../dir/file.ext the parts are:
    RAWDIR = '$rawdir'        # .../dir
    DIR = '$dir'              # ".../dir"
    RAWFILE = '$rawfile'      # .../dir/file.ext
    FILE = '$file'            # ".../dir/file.ext"
    RAWBRANCH = '$rawbranch'  # .../dir/file
    BRANCH = '$branch'        # ".../dir/file"
    NAME = '$name'            # file.ext
    STEM = '$stem'            # file
    EXT = '$ext'              # .ext
    SEP = '$sep'              # /


def removeprefix(string: str, prefix: str) -> str:
    return string[len(prefix):] if string.startswith(prefix) else string


def removesuffix(string: str, suffix: str) -> str:
    return string[:-len(suffix)] if string.endswith(suffix) else string


def print_err(message: str) -> None:
    if display_errors:
        print(f"***| RunMany Error: {message} |***", file=sys.stderr)


class LanguagesData:
    @staticmethod
    def normalize(language: str) -> str:
        return language.strip().lower()

    @staticmethod
    def json_to_class(json_string: str) -> Any:
        return json.loads(json_string, object_hook=lambda d: types.SimpleNamespace(**d))

    @staticmethod
    def get_json_string(languages_json: JsonLike) -> str:
        if languages_json is None:
            return str({})
        elif isinstance(languages_json, dict):  # Assume already valid json dict.
            return json.dumps(languages_json)
        with open(languages_json) as file:  # Assume path like.
            return file.read()

    @staticmethod
    def language_obj_valid(language_obj: Any, all_name: str) -> bool:
        msg = None
        if not hasattr(language_obj, NAME_KEY):
            msg = f'No "{NAME_KEY}" key found.'
        elif LanguagesData.normalize(language_obj.name) == LanguagesData.normalize(all_name):
            msg = f'Language name "{language_obj.name}" cannot match {ALL_NAME_KEY} "{all_name}".'
        elif not hasattr(language_obj, COMMAND_KEY):
            msg = f'No "{COMMAND_KEY}" key found for {language_obj.name}.'
        elif not hasattr(language_obj, EXT_KEY) and Placeholders.EXT in language_obj.command:
            msg = f'No "{EXT_KEY}" key found to fill "{Placeholders.EXT}" placeholder for {language_obj.name} command.'
        if msg:
            print_err(f'{msg} Ignoring language.')
            return False
        return True

    def __init__(self, languages_json: JsonLike) -> None:
        self.settings = self.json_to_class(self.get_json_string(languages_json))
        with open(DEFAULT_LANGUAGES_JSON_FILE) as file:
            self.defaults = self.json_to_class(file.read())

        self.dict: Dict[str, LanguageData] = {}
        for language_obj in itertools.chain(self.default_languages, self.languages):
            if self.language_obj_valid(language_obj, self.all_name):
                self.dict[self.normalize(language_obj.name)] = LanguageData(language_obj, self)

    def __getattr__(self, name: str) -> Any:
        if hasattr(self.settings, name):
            return getattr(self.settings, name)
        return getattr(self.defaults, name)

    def __getitem__(self, language: str) -> Any:
        return self.dict[self.normalize(language)]

    def unpack(self, language: str) -> List[str]:
        language = self.normalize(language)
        if language == self.normalize(self.all_name):
            return list(self.dict.keys())
        return [language]


# Todo? inherit from default_languages too
class LanguageData:
    def __init__(self, language_obj: Any, parent: LanguagesData):
        self.obj = language_obj
        self.parent = parent

    def __getattr__(self, name: str) -> Any:
        if hasattr(self.obj, name):
            return getattr(self.obj, name)
        return getattr(self.parent, name)


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
        return removeprefix(line, COMMENT_PREFIX) == EXIT_SEP or \
            line.startswith(COMMENT_START) and line.endswith(COMMENT_END)

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

    def __init__(self, header: str, content: str, languages_data: LanguagesData, line_number: int) -> None:
        self.header = header.rstrip()
        self.type, start, end = self.get_type_start_end(self.header)
        self.commented = self.header.startswith(COMMENT_PREFIX)

        raw_header = removeprefix(self.header, COMMENT_PREFIX)
        self.is_sep = raw_header in (CODE_SEP, ARGV_SEP, STDIN_SEP)
        self.content = self.strip_content(content, self.type)
        self.line_number = line_number

        self.languages = []
        if not self.is_sep:
            raw_header = removesuffix(removeprefix(raw_header, start), end)
            for language in raw_header.split(LANGUAGE_DIVIDER):
                try:
                    self.languages.extend(languages_data.unpack(language))
                except KeyError:
                    if not self.commented:
                        print_err(f'Language "{language.strip()}" in section header at line {self.line_number}'
                                  ' not found in json. Skipping language.')

    def __str__(self) -> str:
        return f"{self.header}\n{self.content}"

    def __repr__(self) -> str:
        return f"{'//' if self.commented else ''}{self.type.name} " \
               f"{'SEP' if self.is_sep else self.languages} line {self.line_number}"


def section_iterator(file: TextIO, languages_data: LanguagesData) -> Iterator[Union[str, Section]]:
    def current_section() -> Section:
        return Section(cast(str, header), ''.join(section_lines), languages_data, header_line_number)

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
                yield ''.join(section_lines)  # Yield prologue. Only happens once.
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
    def __init__(self, path: str) -> None:
        def quote(s: str) -> str:
            return f'"{s}"'
        p = pathlib.PurePath(path)
        self.rawdir = str(p.parent)
        self.dir = quote(self.rawdir)
        self.rawfile = str(p)
        self.file = quote(self.rawfile)
        self.rawbranch = str(p.with_suffix(''))
        self.branch = quote(self.rawbranch)
        self.name = p.name
        self.stem = p.stem
        self.ext = p.suffix
        self.sep = os.sep


class Run:
    def __init__(self, code_section: Section, argv_section: Optional[Section], stdin_section: Optional[Section],
                 language_data: LanguageData, number: int) -> None:
        self.code_section = code_section
        self.argv_section = argv_section
        self.stdin_section = stdin_section
        self.language_data = language_data
        self.number = number

    def fill_command(self, code_file_name: str) -> str:
        command = cast(str, self.language_data.command)
        pp = PathParts(code_file_name)
        argv = self.argv_section.content if self.argv_section else ''

        if Placeholders.prefix not in command:  # Then assume we can tack on file and argv.
            command += f' {pp.file}'
            if argv:
                command += f' {argv}'
        else:
            def replace(placeholder: str, replacement: str) -> None:
                nonlocal command
                command = command.replace(placeholder, replacement)
            replace(Placeholders.RAWDIR, pp.rawdir)
            replace(Placeholders.DIR, pp.dir)
            replace(Placeholders.RAWFILE, pp.rawfile)
            replace(Placeholders.FILE, pp.file)
            replace(Placeholders.RAWBRANCH, pp.rawbranch)
            replace(Placeholders.BRANCH, pp.branch)
            replace(Placeholders.NAME, pp.name)
            replace(Placeholders.STEM, pp.stem)
            replace(Placeholders.EXT, pp.ext)
            replace(Placeholders.SEP, pp.sep)
            replace(Placeholders.ARGV, argv)
        return command

    @staticmethod
    def output_section(name: str, section: Optional[Section] = None) -> str:
        content = ''
        if section:
            name += f' at line {section.line_number + 1}'
            content = '\n' + section.content.strip('\r\n')
        return f'{f" {name} ":{OUTPUT_FILL}^{OUTPUT_FILL_WIDTH}}{content}'

    def output(self, command: str, stdout: str, exit_code: Union[int, str]) -> str:
        parts = []

        header = f'{self.number}. {self.language_data.name}'
        if exit_code != 0:
            header += f' [exit code {exit_code}]'
        if self.language_data.show_command:
            header += f' {command}'
        parts.append(header)

        if self.language_data.show_code:
            parts.append(self.output_section('code', self.code_section))
        if self.argv_section and self.language_data.show_argv:
            parts.append(self.output_section('argv', self.argv_section))
        if self.stdin_section and self.language_data.show_stdin:
            parts.append(self.output_section('stdin', self.stdin_section))
        if self.language_data.show_output:
            parts.append(self.output_section('output'))
            parts.append(stdout + '\n')

        return '\n'.join(parts)

    def get_stderr(self) -> int:
        if self.language_data.stderr in STDERR_NZEC:
            return subprocess.PIPE
        elif self.language_data.stderr in STDERR_NEVER:
            return subprocess.DEVNULL
        else:
            return subprocess.STDOUT

    def run(self, directory: str) -> Tuple[str, bool]:
        with NamedTemporaryFile(mode='w', suffix=self.language_data.ext, dir=directory, delete=False) as code_file:
            code_file.write(self.code_section.content)
            code_file_name = code_file.name

        command = self.fill_command(code_file_name)
        stdin = self.stdin_section.content if self.stdin_section else None

        try:
            result = subprocess.run(command, input=stdin, timeout=self.language_data.timeout,
                                    shell=True, text=True, stdout=subprocess.PIPE, stderr=self.get_stderr())
            stdout = result.stdout
            exit_code: Union[int, str] = result.returncode
            if exit_code != 0 and self.language_data.stderr in STDERR_NZEC:
                stdout += result.stderr
        except subprocess.TimeoutExpired:
            stdout = f'TIMED OUT OF {self.language_data.timeout}s LIMIT'
            exit_code = 'T'

        output = self.output(command, stdout, exit_code)
        return output, exit_code == 0


def prologue(content: str) -> str:
    return f'{OUTPUT_DIVIDER}\nRunMany Result: {content.strip()}\n{OUTPUT_DIVIDER}\n\n'


def epilogue(total: int, successful: int) -> str:
    info = f'{successful}/{total} program{"" if total == 1 else "s"} successfully run'
    if successful < total:
        info += f'. {total - successful} failed due to non-zero exit code or timeout.'
    else:
        info += '!'
    return f'{OUTPUT_DIVIDER}\n{info}\n{OUTPUT_DIVIDER}'


def run_iterator(file: TextIO, languages_data: LanguagesData) -> Iterator[Union[str, Run]]:
    lead_section: Optional[Section] = None
    argvs: DefaultDict[str, List[Optional[Section]]] = defaultdict(lambda: [None])
    stdins: DefaultDict[str, List[Optional[Section]]] = defaultdict(lambda: [None])
    number = 1

    for section in section_iterator(file, languages_data):
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
                        yield Run(section, argv_section, stdin_section, languages_data[language], number)
                        number += 1


def runmanyf(file: TextIO, many_file: PathLike, languages_json: JsonLike = None, string: bool = False) -> None:
    with redirect_stdout(file):
        languages_data = LanguagesData(languages_json)
        total, successful = 0, 0

        context_manager = io.StringIO(cast(str, many_file)) if string else open(many_file)
        with context_manager as manyfile, TemporaryDirectory() as directory:
            for run in run_iterator(manyfile, languages_data):
                if isinstance(run, str):
                    if languages_data.show_prologue:
                        print(prologue(run))
                else:
                    output, success = run.run(directory)
                    print(output)
                    total += 1
                    if success:
                        successful += 1
            if languages_data.show_epilogue:
                print(epilogue(total, successful))


def runmanys(many_file: PathLike, languages_json: JsonLike = None, string: bool = False) -> str:
    file = io.StringIO()
    runmanyf(file, many_file, languages_json, string)
    file.seek(0)
    return file.read()


def runmany(many_file: PathLike, languages_json: JsonLike = None, output_file: Optional[PathLike] = None,
            string: bool = False) -> None:
    with nullcontext(sys.stdout) if output_file is None else open(output_file, 'w') as file:
        runmanyf(file, many_file, languages_json, string)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='runmany', description='Run a .many file.')
    parser.add_argument('input', help='the .many file to be run')
    parser.add_argument('-j', '--json', help='the languages .json file to use', metavar='<file>')
    parser.add_argument('-o', '--output', help='the file the output is redirected to', metavar='<file>')
    args = parser.parse_args()
    runmany(args.input, args.json, args.output)
