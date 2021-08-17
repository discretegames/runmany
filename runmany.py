from abc import ABC
from dataclasses import dataclass
import os
import json
import enum
import tempfile
import subprocess
from typing import Any, List, Type, Dict, DefaultDict, Union, Optional, TextIO, Iterator, cast
from collections import defaultdict

STARTS = CODE_START, ARGV_START, STDIN_START = '~~~|', '@@@|', '$$$|'
ENDS = CODE_END, ARGV_END, STDIN_END = '|~~~', '|@@@', '|$$$'
SEPS = CODE_SEP, ARGV_SEP, STDIN_SEP = '~~~|~~~', '@@@|@@@', '$$$|$$$'
LANGUAGE_DIVIDER, COMMENT_PREFIX = '|', '!'


class JsonKeys(ABC):
    ALL = 'all'
    TIMEOUT = 'timeout'
    LANGUAGES = 'languages'
    NAME = 'name'
    COMMAND = 'command'
    EXT = 'ext'


class Placeholders(ABC):
    ARGV = '$argv'
    FILE = '$file'
    STEM = '$stem'
    EXT = '$ext'
    DIR = '$dir'  # todo is this one needed?


DEFAULT_JSON_FILE = 'default_languages.json'
DEFAULT_JSON = {
    JsonKeys.ALL: "All",
    JsonKeys.TIMEOUT: 1.0,
    JsonKeys.LANGUAGES: [],
}


def removeprefix(string: str, prefix: str) -> str:
    return string[len(prefix):] if string.startswith(prefix) else string


def removesuffix(string: str, suffix: str) -> str:
    return string[:-len(suffix)] if string.endswith(suffix) else string


@dataclass
class Language:
    name: str
    command: str
    ext: str
    timeout: float
    # todo strict mode? thinking not, only global

    @property
    def name_norm(self) -> str:
        return self.normalize(self.name)

    @staticmethod
    def normalize(name: str) -> str:
        return name.strip().lower()

    @staticmethod  # todo better error text
    def validate_language_json(language_json: Any, all_name: str) -> bool:
        if JsonKeys.NAME not in language_json:
            print(f'No "{JsonKeys.NAME}" key found in {language_json}. Ignoring language.')
            return False
        if Language.normalize(language_json[JsonKeys.NAME]) == Language.normalize(all_name):
            print(f'Language name cannot match all name "{all_name}". Ignoring language.')
            return False
        if JsonKeys.COMMAND not in language_json:
            print(f'No "{JsonKeys.COMMAND}" key found in {language_json}. Ignoring language.')
            return False
        if Placeholders.EXT in language_json[JsonKeys.COMMAND] and JsonKeys.EXT not in language_json:
            print(f'No extension defined to fill placeholder "{Placeholders.EXT}". Ignoring language.')
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
            return languages_json.get(key, DEFAULT_JSON[key])

        all_ = get_default(JsonKeys.ALL)
        default_timeout = get_default(JsonKeys.TIMEOUT)

        languages = []
        for language_json in get_default(JsonKeys.LANGUAGES):
            if Language.validate_language_json(language_json, all_):
                languages.append(Language.from_json(language_json, default_timeout))

        return LanguagesData(all_, languages)

    def __init__(self, all_: str, languages: List[Language]) -> None:
        self.all = all_
        self.dict = {language.name_norm: language for language in languages}

    def unpack_language(self, language: str) -> List[str]:
        if Language.normalize(language) == Language.normalize(self.all):
            return list(self.dict.keys())
        return [self[language].name_norm]

    def __getitem__(self, language: str) -> Language:
        return self.dict[Language.normalize(language)]


class SectionType(enum.Enum):
    ARGV = enum.auto()
    CODE = enum.auto()
    STDIN = enum.auto()


class Section:
    def __init__(self, header: str, content: str, languages_data: LanguagesData, line_number: int) -> None:
        self.header = header.rstrip()
        # TODO smarter stripping, always for argv, kinda stdin, never for code
        self.content = content
        self.line_number = line_number
        self.commented = self.header.startswith(COMMENT_PREFIX)

        header = removeprefix(self.header, COMMENT_PREFIX)
        self.is_sep = header in SEPS

        if header == CODE_SEP or header.startswith(CODE_START):
            self.type, start, end = SectionType.CODE, CODE_START, CODE_END
        elif header == ARGV_SEP or header.startswith(ARGV_START):
            self.type, start, end = SectionType.ARGV, ARGV_START, ARGV_END
        elif header == STDIN_SEP or header.startswith(STDIN_START):
            self.type, start, end = SectionType.STDIN, STDIN_START, STDIN_END

        self.languages = []
        if not self.is_sep:
            header = removesuffix(removeprefix(header, start), end)
            for language in header.split(LANGUAGE_DIVIDER):
                try:
                    self.languages.extend(languages_data.unpack_language(language))
                except KeyError:
                    print(f'Language "{language.strip()}" not found. Skipping.')

    def __str__(self) -> str:
        return f"{self.header}\n{self.content}"

    def __repr__(self) -> str:
        return f"{'//' if self.commented else ''}{self.type.name} " \
               f"{'SEP' if self.is_sep else self.languages} line {self.line_number}"

    @ staticmethod
    def line_is_header(line: str) -> bool:
        line = removeprefix(line.rstrip(), COMMENT_PREFIX)
        return line in SEPS or any(line.startswith(s) and line.endswith(e) for s, e in zip(STARTS, ENDS))


class Run:
    def __init__(self, number: int, language: Language,
                 code_section: Section, argv_section: Optional[Section], stdin_section: Optional[Section]) -> None:
        self.number = number
        self.language = language
        self.code_section = code_section
        self.argv_section = argv_section
        self.stdin_section = stdin_section
        self.stdout = 'NOT YET RUN'

    def fill_command(self, code_file_name: str) -> str:
        command = self.language.command
        file = f'"{code_file_name}"'
        argv = self.argv_section.content if self.argv_section else ''

        if Placeholders.FILE in command:
            command = command.replace(Placeholders.FILE, file)
        else:
            command += f' {file}'

        if Placeholders.ARGV in command:
            command = command.replace(Placeholders.ARGV, argv)
        elif argv:
            command += f' {argv}'

        return command

    def get_stdin(self) -> Optional[str]:
        if self.stdin_section:
            stdin = self.stdin_section.content
            return stdin if stdin.endswith('\n') else stdin + '\n'
        return None

    def run(self) -> None:
        # todo probably put this in a try
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as code_file:
            code_file.write(self.code_section.content)
            code_file_name = code_file.name

        try:
            result = subprocess.run(self.fill_command(code_file_name), shell=True, text=True, timeout=self.language.timeout,
                                    input=self.get_stdin(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.stdout = result.stdout
        except subprocess.TimeoutExpired:
            self.stdout = f'TIMED OUT OF {self.language.timeout}s LIMIT'  # todo format nicer?
        finally:
            os.remove(code_file_name)  # todo should this be in another try?

    def __str__(self) -> str:  # todo make printing prettier
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


def section_iterator(file: TextIO, languages_data: LanguagesData) -> Iterator[Section]:
    def current_section() -> Section:
        return Section(cast(str, header), ''.join(section_lines), languages_data, header_line_number)

    header: Optional[str] = None
    header_line_number = 0
    section_lines: List[str] = []
    for line_number, line in enumerate(file, 1):
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


def run_iterator(file: TextIO, languages_data: LanguagesData) -> Iterator[Run]:
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
            if not lead_section:  # TODO better/optional error messages everywhere
                print(f'Lead section missing. Skipping {repr(section)}')
                continue
            elif lead_section and section.type is not lead_section.type:
                print(f'No matching lead section. Skipping {repr(section)}')
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
                        run.run()
                        yield run
                        number += 1


def load_languages_json(languages_json_file: str) -> Any:
    try:
        with open(languages_json_file) as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return DEFAULT_JSON


def runmany(many_file: str, languages_json_file: str = DEFAULT_JSON_FILE) -> None:
    languages_json = load_languages_json(languages_json_file)
    with open(many_file) as file:
        for run in run_iterator(file, LanguagesData.from_json(languages_json)):
            print(run)


if __name__ == "__main__":
    runmany('helloworld.many')
