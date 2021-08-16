import json
from typing import Any, List, Dict, DefaultDict, Optional, TextIO, Iterator, cast
from enum import Enum, auto
from collections import defaultdict
from dataclasses import dataclass

STARTS = CODE_START, ARGV_START, STDIN_START = '~~~|', '@@@|', '$$$|'
ENDS = CODE_END, ARGV_END, STDIN_END = '|~~~', '|@@@', '|$$$'
SEPS = CODE_SEP, ARGV_SEP, STDIN_SEP = '~~~|~~~', '@@@|@@@', '$$$|$$$'
LANGUAGE_DIVIDER, COMMENT_PREFIX = '|', '!'

FILE_PLACEHOLDER, ARGV_PLACEHOLDER = '$file', '$argv'
FILE_MISSING_APPEND = f' {FILE_PLACEHOLDER}'
ARGV_MISSING_APPEND = f' {ARGV_PLACEHOLDER}'

ALL_KEY = 'all'
LANGUAGES_KEY, NAME_KEY, COMMAND_KEY = 'languages', 'name', 'command'
DEFAULT_LANGUAGES_JSON_FILE = 'default_languages.json'
DEFAULT_LANGUAGES_JSON = {
    ALL_KEY: "All",
    LANGUAGES_KEY: [],
}


def removeprefix(string: str, prefix: str) -> str:
    return string[len(prefix):] if string.startswith(prefix) else string


def removesuffix(string: str, suffix: str) -> str:
    return string[:-len(suffix)] if string.endswith(suffix) else string


def normalize_name(name: str) -> str:
    return name.strip().lower()


class SectionType(Enum):
    CODE = auto()
    ARGV = auto()
    STDIN = auto()


class Section:
    def __init__(self, header: str, content: str, all_name: str, all_languages: List[str], line_number: int) -> None:
        self.header = header.rstrip()
        self.content = content  # todo strip blank lines here
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
                language = normalize_name(language)
                if language == all_name:
                    self.languages.extend(all_languages)
                else:
                    self.languages.append(language)

    def __str__(self) -> str:
        return f"{self.header}\n{self.content}"

    def __repr__(self) -> str:
        return f"{'//' if self.commented else ''}{self.type.name} " \
               f"{'SEP' if self.is_sep else self.languages} line {self.line_number}"

    @staticmethod
    def line_is_header(line: str) -> bool:
        line = removeprefix(line.rstrip(), COMMENT_PREFIX)
        return line in SEPS or any(line.startswith(s) and line.endswith(e) for s, e in zip(STARTS, ENDS))


def section_iterator(file: TextIO, all_name: str, all_languages: List[str]) -> Iterator[Section]:
    def current_section() -> Section:
        return Section(cast(str, header), ''.join(section_lines), all_name, all_languages, header_line_number)

    header: Optional[str] = None
    header_line_number = 0
    section_lines: List[str] = []
    for line_number, line in enumerate(file, 1):
        if Section.line_is_header(line):
            if header is not None:
                yield current_section()
            header = line
            header_line_number = line_number
            section_lines = []
        else:
            section_lines.append(line)

    if header is not None:
        yield current_section()


@dataclass
class Run:
    language: str
    command: str
    code: str
    argv: str
    stdin: str
    output: Optional[str] = None

    def run(self) -> None:
        pass  # BIG TODO


def run_iterator(file: TextIO, languages_json: Any, languages_dict: Dict[str, Any]) -> Iterator[Run]:
    lead_section: Optional[Section] = None
    argvs: DefaultDict[str, List[str]] = defaultdict(lambda: [''])
    stdins: DefaultDict[str, List[str]] = defaultdict(lambda: [''])

    def update(argvs_or_stdins: DefaultDict[str, List[str]]) -> None:
        for language in cast(Section, lead_section).languages:
            if not section.is_sep:
                argvs_or_stdins[language].clear()
            argvs_or_stdins[language].append(section.content)

    for section in section_iterator(file, normalize_name(languages_json[ALL_KEY]), list(languages_dict.keys())):
        if section.commented:
            continue

        if section.is_sep:
            if lead_section is None:  # TODO better/optional error messages everywhere
                print(f'Lead section missing. Skipping {repr(section)}')
                continue
            elif lead_section is not None and section.type is not lead_section.type:
                print(f'No matching lead section. Skipping {repr(section)}')
                continue
        else:
            lead_section = section

        if section.type is SectionType.ARGV:
            update(argvs)
        elif section.type is SectionType.STDIN:
            update(stdins)
        elif section.type is SectionType.CODE:
            for lang in lead_section.languages:
                lang_obj = languages_dict[lang]
                for argv in argvs[lang]:
                    for stdin in stdins[lang]:
                        run = Run(lang_obj[NAME_KEY], lang_obj[COMMAND_KEY], section.content, argv, stdin)
                        run.run()
                        yield run


def clean_languages_json(languages_json: Any) -> Any:
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
        if normalize_name(language_obj[NAME_KEY]) == normalize_name(languages_json[ALL_KEY]):
            print(f'Language name cannot match name for all. Ignoring language.')
            continue
        languages.append(language_obj)
    languages_json[LANGUAGES_KEY] = languages
    return languages_json


def load_languages_json(languages_json_file: str) -> Any:
    try:
        with open(languages_json_file) as file:
            return clean_languages_json(json.load(file))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_LANGUAGES_JSON


def make_languages_dict(languages_json: Any) -> Dict[str, Any]:
    languages_dict = {}
    for language_obj in languages_json[LANGUAGES_KEY]:
        languages_dict[normalize_name(language_obj[NAME_KEY])] = language_obj
    return languages_dict


def runmany(many_file: str, languages_json_file: str = DEFAULT_LANGUAGES_JSON_FILE) -> None:
    languages_json = load_languages_json(languages_json_file)
    languages_dict = make_languages_dict(languages_json)
    with open(many_file) as file:
        for run in run_iterator(file, languages_json, languages_dict):
            print(run)


if __name__ == "__main__":
    runmany('test2.many')
