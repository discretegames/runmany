import json
import enum
import subprocess
import os
import sys
from abc import ABC
from tempfile import TemporaryDirectory, NamedTemporaryFile
from dataclasses import dataclass
from typing import Any, List, Tuple, DefaultDict, Optional, TextIO, Iterator, cast
from collections import defaultdict
from pathlib import PurePath

CODE_START, ARGV_START, STDIN_START = '~~~|', '@@@|', '$$$|'
CODE_END, ARGV_END, STDIN_END = '|~~~', '|@@@', '|$$$'
CODE_SEP, ARGV_SEP, STDIN_SEP = '~~~|~~~', '@@@|@@@', '$$$|$$$'
COMMENT_START, COMMENT_END, EXIT_SEP = '!!!|', '|!!!', '%%%|%%%'
LANGUAGE_DIVIDER, COMMENT_PREFIX = '|', '!'


class JsonKeys(ABC):
    ALL_NAME = 'all_name'
    TIMEOUT = 'timeout'
    LANGUAGES = 'languages'
    NAME = 'name'
    COMMAND = 'command'
    EXT = 'ext'


class Placeholders(ABC):
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


LANGUAGES_JSON_FILE = 'languages.json'
DEFAULT_LANGUAGES_JSON = {
    JsonKeys.ALL_NAME: "All",
    JsonKeys.TIMEOUT: 1.0,
    JsonKeys.LANGUAGES: [],
}


def removeprefix(string: str, prefix: str) -> str:
    return string[len(prefix):] if string.startswith(prefix) else string


def removesuffix(string: str, suffix: str) -> str:
    return string[:-len(suffix)] if string.endswith(suffix) else string


def print_err(message: str) -> None:
    print(f"***| Runmany Error: {message} |***", file=sys.stderr)


@dataclass
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
        name = language_json[JsonKeys.NAME]
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


class LanguagesData:
    @staticmethod
    def from_json(languages_json: Any) -> 'LanguagesData':
        def get_default(key: str) -> Any:
            return languages_json.get(key, DEFAULT_LANGUAGES_JSON[key])

        all_name = get_default(JsonKeys.ALL_NAME)
        default_timeout = get_default(JsonKeys.TIMEOUT)

        languages = []
        for language_json in get_default(JsonKeys.LANGUAGES):
            if Language.validate_language_json(language_json, all_name):
                languages.append(Language.from_json(language_json, default_timeout))

        return LanguagesData(all_name, languages)

    def __init__(self, all_name: str, languages: List[Language]) -> None:
        self.all_name = all_name
        self.dict = {language.name_norm: language for language in languages}

    def unpack_language(self, language: str) -> List[str]:
        if Language.normalize(language) == Language.normalize(self.all_name):
            return list(self.dict.keys())
        return [self[language].name_norm]

    def __getitem__(self, language: str) -> Language:
        return self.dict[Language.normalize(language)]


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
                    self.languages.extend(languages_data.unpack_language(language))
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
        p = PurePath(path)
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

    def __str__(self) -> str:
        lines = []
        lines.append(
            f'{CODE_START} {self.language.name} Output [#{self.number} line {self.code_section.line_number}] {CODE_END}\n')
        if self.argv_section:
            lines.append(self.argv_section.content)
            lines.append(f'\n[line {self.argv_section.line_number} argv]\n')
        if self.stdin_section:
            lines.append(self.stdin_section.content)
            lines.append(f'\n[line {self.stdin_section.line_number} stdin]\n')
        lines.append(self.stdout)

        return ''.join(lines)

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

        print(command)
        return command

    def run(self, tmp_dir: str) -> None:
        with NamedTemporaryFile(mode='w', suffix=self.language.ext, dir=tmp_dir, delete=False) as code_file:
            code_file.write(self.code_section.content)
            code_file_name = code_file.name

        try:
            stdin = self.stdin_section.content if self.stdin_section else None
            result = subprocess.run(self.fill_command(code_file_name), input=stdin, timeout=self.language.timeout,
                                    shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            # , capture_output=True)
            print(result.returncode)  # todo clean up
            self.stdout = result.stdout
        except subprocess.TimeoutExpired:
            self.stdout = f'TIMED OUT OF {self.language.timeout}s LIMIT'  # todo T exit code
        finally:
            os.remove(code_file_name)  # Clean up what we can. Whole directory will be cleaned up eventually.


def section_iterator(file: TextIO, languages_data: LanguagesData) -> Iterator[Section]:
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
            if header:
                yield current_section()
            header = line
            header_line_number = line_number
            section_lines = []
        else:
            section_lines.append(line)

    if header:
        yield current_section()


def run_iterator(file: TextIO, tmp_dir: str, languages_data: LanguagesData) -> Iterator[Run]:
    lead_section: Optional[Section] = None
    argvs: DefaultDict[str, List[Optional[Section]]] = defaultdict(lambda: [None])
    stdins: DefaultDict[str, List[Optional[Section]]] = defaultdict(lambda: [None])
    number = 1

    def update(argvs_or_stdins: DefaultDict[str, List[Optional[Section]]]) -> None:
        for language in cast(Section, lead_section).languages:
            if not section.is_sep:
                argvs_or_stdins[language].clear()
            argvs_or_stdins[language].append(section)

    for section in section_iterator(file, languages_data):
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
            update(argvs)
        elif section.type is SectionType.STDIN:
            update(stdins)
        elif section.type is SectionType.CODE:
            for language in lead_section.languages:
                for argv_section in argvs[language]:
                    for stdin_section in stdins[language]:
                        run = Run(number, languages_data[language], section, argv_section, stdin_section)
                        run.run(tmp_dir)
                        yield run
                        number += 1


def load_languages_json(languages_json_file: str) -> Any:
    try:
        with open(languages_json_file) as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return DEFAULT_LANGUAGES_JSON


def runmany(many_file: str, languages_json_file: str = LANGUAGES_JSON_FILE) -> None:
    languages_json = load_languages_json(languages_json_file)
    with open(many_file) as file:
        with TemporaryDirectory() as tmp_dir:
            for run in run_iterator(file, tmp_dir, LanguagesData.from_json(languages_json)):
                print(run)


if __name__ == "__main__":
    runmany('test.many')
