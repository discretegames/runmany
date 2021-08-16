import os
import json
import enum
import tempfile
import subprocess
from typing import Any, List, DefaultDict, Union, Optional, TextIO, Iterator, cast
from collections import defaultdict

STARTS = CODE_START, ARGV_START, STDIN_START = '~~~|', '@@@|', '$$$|'
ENDS = CODE_END, ARGV_END, STDIN_END = '|~~~', '|@@@', '|$$$'
SEPS = CODE_SEP, ARGV_SEP, STDIN_SEP = '~~~|~~~', '@@@|@@@', '$$$|$$$'
LANGUAGE_DIVIDER, COMMENT_PREFIX = '|', '!'
FILE_PLACEHOLDER, ARGV_PLACEHOLDER = '$file', '$argv'

ALL_KEY, STRIP_KEY = 'all', 'strip'
LANGUAGES_KEY, NAME_KEY, COMMAND_KEY = 'languages', 'name', 'command'
DEFAULT_LANGUAGES_JSON_FILE = 'default_languages.json'
DEFAULT_LANGUAGES_JSON = {
    ALL_KEY: "All",
    STRIP_KEY: True,
    LANGUAGES_KEY: [],
}


def removeprefix(string: str, prefix: str) -> str:
    return string[len(prefix):] if string.startswith(prefix) else string


def removesuffix(string: str, suffix: str) -> str:
    return string[:-len(suffix)] if string.endswith(suffix) else string


class LanguagesData:
    @staticmethod
    def normalize(language_name: str) -> str:
        return language_name.strip().lower()

    @staticmethod
    def load_json(languages_json_file: str) -> Any:
        try:
            with open(languages_json_file) as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError):
            return DEFAULT_LANGUAGES_JSON

    @staticmethod
    def clean_json(languages_json: Any) -> Any:
        for key, value in DEFAULT_LANGUAGES_JSON.items():
            languages_json.setdefault(key, value)
        languages = []
        for language_obj in languages_json[LANGUAGES_KEY]:
            if NAME_KEY not in language_obj:
                print(f'No "{NAME_KEY}" key found in {language_obj}. Ignoring language.')
                continue
            if COMMAND_KEY not in language_obj:
                print(f'No "{COMMAND_KEY}" key found in {language_obj}. Ignoring language.')
                continue
            if LanguagesData.normalize(language_obj[NAME_KEY]) == LanguagesData.normalize(languages_json[ALL_KEY]):
                print(f'Language name cannot match name for all. Ignoring language.')
                continue
            languages.append(language_obj)
        languages_json[LANGUAGES_KEY] = languages
        return languages_json

    def __init__(self, languages_json_file: str) -> None:
        self.json = self.clean_json(self.load_json(languages_json_file))
        self.dict = {}
        for language_obj in self.json[LANGUAGES_KEY]:
            self.dict[self.normalize(language_obj[NAME_KEY])] = language_obj
        self.all_name_normalized = self.normalize(cast(str, self.json[ALL_KEY]))
        self.all_languages = list(self.dict.keys())

    def get_languages(self, language: str) -> List[str]:
        language = self.normalize(language)
        if language == self.all_name_normalized:
            return self.all_languages
        return [language] if language in self.dict else []

    def get_name(self, language: str) -> str:
        return cast(str, self.dict[self.normalize(language)][NAME_KEY])

    def get_command(self, language: str) -> str:
        return cast(str, self.dict[self.normalize(language)][COMMAND_KEY])

    def strip_content(self, content: str) -> str:  # todo think about always stripping argv, also preformat stdin
        return content.strip('\r\n') if self.json[STRIP_KEY] else content


class SectionType(enum.Enum):
    ARGV = enum.auto()
    CODE = enum.auto()
    STDIN = enum.auto()


class Section:
    def __init__(self, header: str, content: str, languages_data: LanguagesData, line_number: int) -> None:
        self.header = header.rstrip()
        self.content = languages_data.strip_content(content)
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
                languages = languages_data.get_languages(language)
                if languages:
                    self.languages.extend(languages)
                else:
                    print(f'Language "{language}" not found. Skipping.')

    def __str__(self) -> str:
        return f"{self.header}\n{self.content}"

    def __repr__(self) -> str:
        return f"{'//' if self.commented else ''}{self.type.name} " \
               f"{'SEP' if self.is_sep else self.languages} line {self.line_number}"

    @staticmethod
    def line_is_header(line: str) -> bool:
        line = removeprefix(line.rstrip(), COMMENT_PREFIX)
        return line in SEPS or any(line.startswith(s) and line.endswith(e) for s, e in zip(STARTS, ENDS))


class Run:
    def __init__(self, number: int, language: str, command: str,
                 code_section: Section, argv_section: Optional[Section], stdin_section: Optional[Section]) -> None:
        self.number = number
        self.language = language
        self.command = command
        self.code_section = code_section
        self.argv_section = argv_section
        self.stdin_section = stdin_section
        self.stdout = 'NOT YET RUN'

    def fill_command(self, code_file_name: str) -> str:
        command = self.command
        file = f"'{code_file_name}'"  # TODO quotes and spaces not working, wth?
        file = r"'C:\Users\r\Desktop\TenLanguages\test it.py'"
        argv = self.argv_section.content if self.argv_section else ''

        if FILE_PLACEHOLDER in command:
            command = command.replace(FILE_PLACEHOLDER, file)
        else:
            command += f' {file}'

        if ARGV_PLACEHOLDER in command:
            command = command.replace(ARGV_PLACEHOLDER, argv)
        elif argv:
            command += f' {argv}'

        print(repr(command))
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

        timeout = 1  # todo add to json

        try:
            result = subprocess.run(self.fill_command(code_file_name), shell=True, text=True, timeout=timeout,
                                    input=self.get_stdin(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.stdout = result.stdout
        except subprocess.TimeoutExpired:
            self.stdout = f'TIMED OUT OF {timeout}s LIMIT'  # todo format nicer?
        finally:
            os.remove(code_file_name)  # todo should this be in another try?

    def __str__(self) -> str:  # todo make printing prettier
        lines = []
        lines.append(
            f'{CODE_START} {self.language} Output [#{self.number} line {self.code_section.line_number}] {CODE_END}\n')
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
                name, command = languages_data.get_name(language), languages_data.get_command(language)
                for argv_section in argvs[language]:
                    for stdin_section in stdins[language]:
                        run = Run(number, name, command, section, argv_section, stdin_section)
                        run.run()
                        yield run
                        number += 1


def runmany(many_file: str, languages_json_file: str = DEFAULT_LANGUAGES_JSON_FILE) -> None:
    with open(many_file) as file:
        for run in run_iterator(file, LanguagesData(languages_json_file)):
            print(run)


if __name__ == "__main__":
    runmany('test2.many')
