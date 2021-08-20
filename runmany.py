import os
import io
import sys
import abc
import json
import enum
import types
import pathlib
import tempfile
import argparse
import subprocess
import dataclasses
import collections
from typing import Any, List, DefaultDict, Tuple, Union, Optional, TextIO, Iterator, cast

display_errors = True  # The only mutating global.

PathLike = Union[str, bytes, os.PathLike[Any]]
JsonLike = Union[None, str, bytes, os.PathLike[Any], Any]

CODE_START, ARGV_START, STDIN_START = '~~~|', '@@@|', '$$$|'
CODE_END, ARGV_END, STDIN_END = '|~~~', '|@@@', '|$$$'
CODE_SEP, ARGV_SEP, STDIN_SEP = '~~~|~~~', '@@@|@@@', '$$$|$$$'
COMMENT_START, COMMENT_END, EXIT_SEP = '!!!|', '|!!!', '%%%|%%%'
LANGUAGE_DIVIDER, COMMENT_PREFIX = '|', '!'
OUTPUT_FILL, OUTPUT_FILL_WIDTH = '-', 60
OUTPUT_DIVIDER = OUTPUT_FILL * int(1.5 * OUTPUT_FILL_WIDTH)
DEFAULT_LANGUAGES_JSON_FILE = 'default_languages.json'


class JsonKeys(abc.ABC):  # todo can mostly remove
    ALL_NAME = 'all_name'
    STDERR = 'stderr'
    TIMEOUT = 'timeout'
    LANGUAGES = 'languages'
    NAME = 'name'
    COMMAND = 'command'
    EXT = 'ext'
    SHOW_COMMAND = 'show_command'
    SHOW_CODE = 'show_code'
    SHOW_ARGV = 'show_argv'
    SHOW_STDIN = 'show_stdin'
    SHOW_OUTPUT = 'show_output'
    SHOW_ERRORS = 'show_errors'
    SHOW_PROLOGUE = 'show_prologue'
    SHOW_EPILOGUE = 'show_epilogue'


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


@dataclasses.dataclass
class Language:
    name: str
    command: str
    ext: str
    timeout: float

    @property
    def name_norm(self) -> str:
        return self.normalize(self.name)

    @staticmethod
    def normalize(name: str) -> str:
        return name.strip().lower()

    @staticmethod
    def validate_language_json(language_json: Any, all_name: str) -> bool:
        name = language_json[JsonKeys.NAME]  # todo bad anyway
        if JsonKeys.NAME not in language_json:
            print_err(f'No "{JsonKeys.NAME}" key found in {json.dumps(language_json)}. Ignoring language.')
            return False
        if Language.normalize(name) == Language.normalize(all_name):
            print_err(f'Language name "{name}" cannot match {JsonKeys.ALL_NAME} "{all_name}". Ignoring language.')
            return False
        if JsonKeys.COMMAND not in language_json:
            print_err(f'No "{JsonKeys.COMMAND}" key found for {name}. Ignoring language.')
            return False
        if Placeholders.EXT in language_json[JsonKeys.COMMAND] and JsonKeys.EXT not in language_json:
            print_err(f'No "{JsonKeys.EXT}" key found to fill "{Placeholders.EXT}" placeholder for {name} command.'
                      ' Ignoring language.')
            return False
        return True

    @staticmethod
    def from_json(language_json: Any, default_timeout: float) -> 'Language':
        name = language_json[JsonKeys.NAME]
        command = language_json[JsonKeys.COMMAND]
        ext = language_json.get(JsonKeys.EXT, '')
        timeout = language_json.get(JsonKeys.TIMEOUT, default_timeout)
        return Language(name, command, ext, timeout)


class StderrOption(enum.Enum):
    ALWAYS = enum.auto()
    NEVER = enum.auto()
    NZEC = enum.auto()

    @staticmethod
    def from_json(stderr_json: Any) -> 'StderrOption':
        if stderr_json is True or stderr_json == 'always':
            return StderrOption.ALWAYS
        elif stderr_json is False or stderr_json == 'never':
            return StderrOption.NEVER
        else:
            return StderrOption.NZEC


class LanguagesDataA:
    @staticmethod
    def from_json(languages_json: Any) -> 'LanguagesData':
        def get_backup(key: str) -> Any:
            return languages_json.get(key, BACKUP_LANGUAGES_JSON[key])

        all_name = get_backup(JsonKeys.ALL_NAME)
        stderr_op = StderrOption.from_json(get_backup(JsonKeys.STDERR))
        default_timeout = get_backup(JsonKeys.TIMEOUT)

        languages = []
        for language_json in get_backup(JsonKeys.LANGUAGES):
            if Language.validate_language_json(language_json, all_name):
                languages.append(Language.from_json(language_json, default_timeout))

        shows = JsonKeys.SHOW_COMMAND, JsonKeys.SHOW_CODE, JsonKeys.SHOW_ARGV, JsonKeys.SHOW_STDIN, \
            JsonKeys.SHOW_OUTPUT, JsonKeys.SHOW_ERRORS, JsonKeys.SHOW_PROLOGUE, JsonKeys.SHOW_EPILOGUE
        return LanguagesData(all_name, stderr_op, languages, *map(get_backup, shows))

    def __init__(self, all_name: str, stderr_op: StderrOption, languages: List[Language],
                 show_command: bool, show_code: bool, show_argv: bool, show_stdin: bool,
                 show_output: bool, show_errors: bool, show_prologue: bool, show_epilogue: bool) -> None:
        global display_errors
        display_errors = show_errors

        self.all_name = all_name
        self.stderr_op = stderr_op
        self.dict = {language.name_norm: language for language in languages}

        self.show_command = show_command
        self.show_code = show_code
        self.show_argv = show_argv
        self.show_stdin = show_stdin
        self.show_output = show_output
        self.show_prologue = show_prologue
        self.show_epilogue = show_epilogue

    def __getitem__(self, language: str) -> Language:
        return self.dict[Language.normalize(language)]


def json_to_class(json_string: str) -> Any:
    return json.loads(json_string, object_hook=lambda d: types.SimpleNamespace(**d))


class LanguagesData:
    def __init__(self, languages_json: JsonLike) -> None:
        if languages_json is None:
            json_string = '{}'
        elif isinstance(languages_json, dict):  # Assume already valid json dict.
            json_string = json.dumps(languages_json)
        else:  # Assume path like.
            with open(languages_json) as file:
                json_string = file.read()

        self.settings = json_to_class(json_string)
        with open(DEFAULT_LANGUAGES_JSON_FILE) as file:
            self.defaults = json_to_class(file.read())

        self.dict = {}
        print(self.)

        # Todo
        # make dict of languages with proper normalizing, validation, and shadowing
        # set up self.stderr with enum (getattr only triggers on not found)

    def __getattr__(self, name: str) -> Any:
        if hasattr(self.settings, name):
            return getattr(self.settings, name)
        return getattr(self.defaults, name)


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

    def __init__(self, header: str, content: str, line_number: int, languages_data: LanguagesData) -> None:
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
    def __init__(self, number: int, language: Language,
                 code_section: Section, argv_section: Optional[Section], stdin_section: Optional[Section]) -> None:
        self.number = number
        self.language = language
        self.code_section = code_section
        self.argv_section = argv_section
        self.stdin_section = stdin_section
        self.stdout = 'NOT YET RUN'
        self.exit_code: Union[int, str] = 'N'
        self.command = self.language.command

    def fill_command(self, code_file_name: str) -> str:
        command = self.language.command
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

    def run(self, tmp_dir: str, stderr_op: StderrOption) -> None:
        with tempfile.NamedTemporaryFile(mode='w', suffix=self.language.ext, dir=tmp_dir, delete=False) as code_file:
            code_file.write(self.code_section.content)
            code_file_name = code_file.name

        self.command = self.fill_command(code_file_name)
        stdin = self.stdin_section.content if self.stdin_section else None

        # tod just do the raw check here
        if stderr_op is StderrOption.ALWAYS:
            stderr = subprocess.STDOUT
        elif stderr_op is StderrOption.NEVER:
            stderr = subprocess.DEVNULL
        elif stderr_op is StderrOption.NZEC:
            stderr = subprocess.PIPE

        try:
            result = subprocess.run(self.command, input=stdin, timeout=self.language.timeout,
                                    shell=True, text=True, stdout=subprocess.PIPE, stderr=stderr)
            self.stdout = result.stdout
            if stderr_op is StderrOption.NZEC and result.returncode:
                self.stdout += result.stderr
            self.exit_code = result.returncode
        except subprocess.TimeoutExpired:
            self.stdout = f'TIMED OUT OF {self.language.timeout}s LIMIT'
            self.exit_code = 'T'

    @staticmethod
    def output_section(name: str, section: Optional[Section] = None) -> str:
        content = ''
        if section:
            name += f' at line {section.line_number + 1}'
            content = '\n' + section.content.strip('\r\n')
        return f'{f" {name} ":{OUTPUT_FILL}^{OUTPUT_FILL_WIDTH}}{content}'

    def output(self, languages_data: LanguagesData) -> str:  # todo can pass in language_obj and shadow all props
        parts = []

        header = f'{self.number}. {self.language.name}'
        if self.exit_code:
            header += f' [exit code {self.exit_code}]'
        if languages_data.show_command:
            header += f' {self.command}'
        parts.append(header)

        if languages_data.show_code:
            parts.append(self.output_section('code', self.code_section))
        if self.argv_section and languages_data.show_argv:
            parts.append(self.output_section('argv', self.argv_section))
        if self.stdin_section and languages_data.show_stdin:
            parts.append(self.output_section('stdin', self.stdin_section))
        if languages_data.show_output:
            parts.append(self.output_section('output'))
            parts.append(self.stdout + '\n')

        return '\n'.join(parts)


def prologue(content: str) -> str:
    return f'{OUTPUT_DIVIDER}\nRunMany Result: {content.strip()}\n{OUTPUT_DIVIDER}\n\n'


def epilogue(total: int, successful: int) -> str:
    info = f'{successful}/{total} program{"" if total == 1 else "s"} successfully run'
    if successful < total:
        info += f'. {total - successful} failed due to non-zero exit code or timeout.'
    else:
        info += '!'
    return f'{OUTPUT_DIVIDER}\n{info}\n{OUTPUT_DIVIDER}'


def section_iterator(file: TextIO, languages_data: LanguagesData) -> Iterator[Union[str, Section]]:
    def current_section() -> Section:
        return Section(cast(str, header), ''.join(section_lines), header_line_number, languages_data)

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


# turn back into Run iterator that can also be string fpr prologue? maybe
def output_iterator(file: TextIO, languages_data: LanguagesData, tmp_dir: str) -> Iterator[Tuple[str, bool]]:
    lead_section: Optional[Section] = None
    argvs: DefaultDict[str, List[Optional[Section]]] = collections.defaultdict(lambda: [None])
    stdins: DefaultDict[str, List[Optional[Section]]] = collections.defaultdict(lambda: [None])
    number = 1

    for section in section_iterator(file, languages_data):
        if isinstance(section, str):
            yield section, True
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
                        run = Run(number, languages_data[language], section, argv_section, stdin_section)
                        run.run(tmp_dir, languages_data.stderr_op)
                        yield run.output(languages_data), run.exit_code == 0
                        number += 1


def runmany_to_file(outfile: TextIO, many_file: PathLike, languages_json: JsonLike = None,
                    from_string: bool = False) -> None:
    languages_data = LanguagesData(languages_json)
    total, successful = -1, -1  # -1 to offset prologue.

    with io.StringIO(cast(str, many_file)) if from_string else open(many_file) as file:
        with tempfile.TemporaryDirectory() as tmp_dir:
            for output, success in output_iterator(file, languages_data, tmp_dir):
                if total >= 0:
                    print(output, file=outfile)
                elif languages_data.show_prologue:
                    print(prologue(output), file=outfile)
                total += 1
                if success:
                    successful += 1
            if languages_data.show_epilogue:
                print(epilogue(total, successful), file=outfile)


def runmany(many_file: PathLike, languages_json: JsonLike = None, output_file: Optional[PathLike] = None,
            from_string: bool = False) -> None:
    if output_file is None:
        runmany_to_file(sys.stdout, many_file, languages_json, from_string)
    else:
        with open(output_file, 'w') as outfile:
            runmany_to_file(outfile, many_file, languages_json, from_string)


def runmanys(many_file: PathLike, languages_json: JsonLike = None, from_string: bool = False) -> str:
    string_io = io.StringIO()
    runmany_to_file(string_io, many_file, languages_json, from_string)
    string_io.seek(0)
    return string_io.read()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='runmany', description='Run a .many file.')
    parser.add_argument('input', help='the .many file to be run')
    parser.add_argument('-j', '--json', help='the languages .json file to use', metavar='<file>')
    parser.add_argument('-o', '--output', help='the file the output is redirected to', metavar='<file>')
    args = parser.parse_args()
    runmany(args.input, args.json, args.output)
