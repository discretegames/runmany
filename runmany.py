import json
from typing import Any, List, Dict, DefaultDict, Optional, TextIO, Iterator, cast
from enum import Enum, auto
from collections import defaultdict

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
    def __init__(self, header: str, content: str, line_number: int = 0) -> None:
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

        if self.is_sep:
            self.languages = []
        else:
            header = removesuffix(removeprefix(header, start), end)
            self.languages = [normalize_name(language) for language in header.split(LANGUAGE_DIVIDER)]

    def __str__(self) -> str:
        return f"{self.header}\n{self.content}"

    def __repr__(self) -> str:
        return f"{'//' if self.commented else ''}{self.type.name} " \
               f"{'SEP' if self.is_sep else self.languages} line {self.line_number}"

    @staticmethod
    def line_is_header(line: str) -> bool:
        line = removeprefix(line.rstrip(), COMMENT_PREFIX)
        return line in SEPS or any(line.startswith(s) and line.endswith(e) for s, e in zip(STARTS, ENDS))


def section_iterator(file: TextIO) -> Iterator[Section]:
    header: Optional[str] = None
    header_line_number = 0
    section_lines: List[str] = []
    for line_number, line in enumerate(file, 1):
        if Section.line_is_header(line):
            if header is not None:
                yield Section(header, ''.join(section_lines), header_line_number)
            header = line
            header_line_number = line_number
            section_lines = []
        else:
            section_lines.append(line)

    if header is not None:
        yield Section(header, ''.join(section_lines), header_line_number)


def runone(language: str, command: str, code: str, argv: str, stdin: str) -> None:
    print(f'Running {language}.')


# TODO NOW - refactor json to use list of langs, the redo map to objects, then fix all, then fix runone

# def runall(languages: List[str], argvs: DefaultDict[str, List[str]], stdins: DefaultDict[str, List[str]], code: str) -> None:
#     for lang in languages:
#     if lang not in languages_lower:
#         print(f'Unknown language {lang}. Be sure to add it to languages.json')
#         continue
#     for argv in argvs[lang] if argvs[lang] else ['']:
#         for stdin in stdins[lang] if stdins[lang] else ['']:
#             language_obj = language_dict[lang]
#             runone(language_obj[NAME_KEY], language_obj[COMMAND_KEY],
#                    section.content, argv, stdin)

# def run_iterator(languages)


def output_iterator(file: TextIO, languages_json: Any, languages_dict: Dict[str, Any]) -> Iterator[str]:
    # TODO yield Output class (to make), not str
    lead_section: Optional[Section] = None
    argvs: DefaultDict[str, List[str]] = defaultdict(list)
    stdins: DefaultDict[str, List[str]] = defaultdict(list)

    def update(argvs_or_stdins: DefaultDict[str, List[str]]) -> None:
        for language in cast(Section, lead_section).languages:
            if not section.is_sep:
                argvs_or_stdins[language].clear()
            argvs_or_stdins[language].append(section.content)

    for section in section_iterator(file):
        if section.commented:
            continue

        if section.is_sep:
            if lead_section is None:  # TODO better/optional error messages
                print(f'Lead section missing. Skipping {repr(section)}')
                continue
            elif lead_section is not None and section.type is not lead_section.type:
                print(f'No matching lead section. Skipping {repr(section)}')
                continue
        else:
            lead_section = section

        if section.type is SectionType.CODE:
            print(languages_json)
            print(languages_dict)
            yield repr(section) + '|||' + section.content
            pass
            # yield from run_iterator
            # yield runall(lead_section.languages)  # TODO
        elif section.type is SectionType.ARGV:
            update(argvs)
        elif section.type is SectionType.STDIN:
            update(stdins)


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
        if language_obj[NAME_KEY] == languages_json[ALL_KEY]:
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
        for output in output_iterator(file, languages_json, languages_dict):
            print(output)


if __name__ == "__main__":
    runmany('test2.many')

    # def get_language_commands(language_json_data):
    #     command = language_json_data.get('command')
    #     if command is None:
    #         return {}
    #     names = []
    #     if "name" in language_json_data:
    #         names.append(language_json_data["name"])
    #     names.extend(language_json_data.get("other_names", []))
    #     return {name.strip().lower(): command for name in names}

    # def get_commands_dict(commands_dict):
    #     if commands_dict is None:
    #         with open(DEFAULT_LANGUAGES_JSON) as f:
    #             commands_dict = {}
    #             for language in json.load(f).get("languages", []):
    #                 for name, command in get_language_commands(language).items():
    #                     if name not in commands_dict:
    #                         commands_dict[name] = command
    #     return commands_dict

    # def runone(language, command, snippet):
    #     print(f"{LANG_START} {language} {LANG_END}")
    #     with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
    #         tmp.write(snippet)
    #         tmp_filename = tmp.name
    #     if FILENAME_PLACEHOLDER in command:
    #         command = command.replace(FILENAME_PLACEHOLDER, f'"{tmp_filename}"')
    #     else:
    #         command += f' "{tmp_filename}"'
    #     try:
    #         subprocess.check_call(command)
    #         return True
    #     except subprocess.CalledProcessError:
    #         return False
    #     finally:
    #         os.remove(tmp_filename)

    # def runmany(manyfile, string=False, commands_dict=None):
    #     def tryrun():
    #         nonlocal snippets, runs, successes
    #         if language is not None:
    #             snippets += 1
    #             if language.lower() in commands_dict:
    #                 runs += 1
    #                 if runone(language, commands_dict[language.lower()], ''.join(snippet_lines)):
    #                     successes += 1

    #     snippets, runs, successes = 0, 0, 0
    #     commands_dict = get_commands_dict(commands_dict)

    #     with (io.StringIO if string else open)(manyfile) as f:
    #         language = None
    #         snippet_lines = []
    #         for line in f:
    #             stripped = line.strip()
    #             if stripped.startswith(LANG_START) and stripped.endswith(LANG_END):
    #                 tryrun()
    #                 language = stripped[len(LANG_START):-len(LANG_END)].strip()
    #                 snippet_lines.clear()
    #             elif language is not None:
    #                 snippet_lines.append(line)
    #         tryrun()
    #     print(f"{LANG_START} {snippets} , {runs}, {successes} {LANG_END}")
