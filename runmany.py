import os
import io
import sys
import abc
import ast
import json
import enum
import types
import pathlib
import argparse
import subprocess
from collections import defaultdict
from contextlib import nullcontext, redirect_stdout
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Any, List, Dict, DefaultDict, Tuple, Union, Optional, TextIO, Iterator, cast

display_errors = True  # The only mutating global.

PathLike = Union[str, bytes, 'os.PathLike[Any]']
JsonLike = Union[None, str, bytes, 'os.PathLike[Any]', Any]

DEBUG_ENV_VAR = 'DEBUG_RUNMANY'
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


def debugging() -> bool:
    return DEBUG_ENV_VAR in os.environ and bool(ast.literal_eval(os.environ[DEBUG_ENV_VAR]))


def print_err(message: str) -> None:
    if display_errors:
        print(f"***| RunMany Error: {message} |***", file=sys.stderr)


def removeprefix(string: str, prefix: str) -> str:
    return string[len(prefix):] if string.startswith(prefix) else string


def removesuffix(string: str, suffix: str) -> str:
    return string[:-len(suffix)] if string.endswith(suffix) else string


class LanguageData:
    def __init__(self, language_obj: Any, parent: 'LanguagesData') -> None:
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
            return file.read() or str({})

    def language_obj_valid(self, language_obj: Any, is_default: bool) -> bool:
        end = ". Ignoring language."

        if not hasattr(language_obj, NAME_KEY):
            print_err(f'No "{NAME_KEY}" key found for json list item{end}')
            return False

        if LanguagesData.normalize(language_obj.name) == LanguagesData.normalize(self.all_name):
            print_err(f'Language name "{language_obj.name}" cannot match {ALL_NAME_KEY} "{self.all_name}"{end}')
            return False

        default_obj = self[language_obj.name] if not is_default and language_obj.name in self else None
        if not hasattr(language_obj, COMMAND_KEY) and not hasattr(default_obj, COMMAND_KEY):
            print_err(f'No "{COMMAND_KEY}" key found for {language_obj.name}{end}')
            return False

        return True

    def __init__(self, languages_json: JsonLike) -> None:
        self.data = self.json_to_class(self.get_json_string(languages_json))
        with open(DEFAULT_LANGUAGES_JSON_FILE) as file:
            self.default_data = self.json_to_class(file.read())

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
    @ staticmethod
    def line_is_exit(line: str) -> bool:
        return line.rstrip() == EXIT_SEP

    @ staticmethod
    def line_is_comment(line: str) -> bool:
        line = line.rstrip()
        return removeprefix(line, COMMENT_PREFIX) == EXIT_SEP or \
            line.startswith(COMMENT_START) and line.endswith(COMMENT_END)

    @ staticmethod
    def line_is_header(line: str) -> bool:
        line = removeprefix(line.rstrip(), COMMENT_PREFIX)
        starts = CODE_START, ARGV_START, STDIN_START
        ends = CODE_END, ARGV_END, STDIN_END
        seps = CODE_SEP, ARGV_SEP, STDIN_SEP
        return line in seps or any(line.startswith(s) and line.endswith(e) for s, e in zip(starts, ends))

    @ staticmethod
    def get_type_start_end(header: str) -> Tuple[SectionType, str, str]:
        if header == ARGV_SEP or header.startswith(ARGV_START):
            return SectionType.ARGV, ARGV_START, ARGV_END
        elif header == STDIN_SEP or header.startswith(STDIN_START):
            return SectionType.STDIN, STDIN_START, STDIN_END
        else:
            return SectionType.CODE, CODE_START, CODE_END

    @ staticmethod
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
                 language_data: LanguageData) -> None:
        self.code_section = code_section
        self.argv_section = argv_section
        self.stdin_section = stdin_section
        self.language_data = language_data

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

    @ staticmethod
    def output_section(name: str, section: Optional[Section] = None) -> str:
        content = ''
        if section:
            name += f' at line {section.line_number + 1}'
            content = '\n' + section.content.strip('\r\n')
        return f'{f" {name} ":{OUTPUT_FILL}^{OUTPUT_FILL_WIDTH}}{content}'

    def output(self, command: str, stdout: str, exit_code: Union[int, str], run_number: int) -> str:
        parts = []

        header = f'{run_number}. {self.language_data.name}'
        if exit_code != 0:
            header += f' [exit code {exit_code}]'
        if self.language_data.show_command:
            header += f' > {command}'
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

    def run(self, directory: str, run_number: int) -> Tuple[str, str, bool]:
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

        output = self.output(command, stdout, exit_code, run_number)
        return output, stdout, exit_code == 0


def prologue(content: str) -> str:
    content = content.strip() or 'RunMany Result'
    return f'{OUTPUT_DIVIDER}\n{content}\n{OUTPUT_DIVIDER}\n\n'


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


def run_iterator(file: TextIO, languages_data: LanguagesData) -> Iterator[Union[str, Run]]:
    lead_section: Optional[Section] = None
    argvs: DefaultDict[str, List[Optional[Section]]] = defaultdict(lambda: [None])
    stdins: DefaultDict[str, List[Optional[Section]]] = defaultdict(lambda: [None])

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
                        yield Run(section, argv_section, stdin_section, languages_data[language])


def runmanyf(file: TextIO, many_file: PathLike, languages_json: JsonLike = None, string: bool = False) -> None:
    with redirect_stdout(file):
        languages_data = LanguagesData(languages_json)
        total_runs, successful_runs = 0, 0
        equal_stdouts: DefaultDict[str, List[int]] = defaultdict(list)

        context_manager = io.StringIO(cast(str, many_file)) if string else open(many_file)
        with context_manager as manyfile, TemporaryDirectory() as directory:
            for run in run_iterator(manyfile, languages_data):
                if isinstance(run, str):
                    if languages_data.show_prologue:
                        print(prologue(run))
                else:
                    run_number = total_runs + 1
                    output, stdout, success = run.run(directory, run_number)
                    total_runs += 1
                    successful_runs += success
                    print(output)
                    if languages_data.check_equal:
                        equal_stdouts[stdout].append(run_number)
            if languages_data.show_epilogue:
                print(epilogue(total_runs, successful_runs, equal_stdouts if languages_data.check_equal else None))


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
    if not debugging():
        parser = argparse.ArgumentParser(prog='runmany', description='Run a .many file.')
        parser.add_argument('input', help='the .many file to be run')
        parser.add_argument('-j', '--json', help='the languages .json file to use', metavar='<file>')
        parser.add_argument('-o', '--output', help='the file the output is redirected to', metavar='<file>')
        args = parser.parse_args()
        runmany(args.input, args.json, args.output)
    else:
        runmany('helloworld.many', 'languages.json')
