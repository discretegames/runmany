import json
from typing import Dict, Any, Optional, TextIO, Union, List, Type, Iterator, Tuple
from enum import Enum

# import tempfile
# import subprocess


STARTS = CODE_START, ARGV_START, STDIN_START = '~~~|', '@@@|', '$$$|'
ENDS = CODE_END, ARGV_END, STDIN_END = '|~~~', '|@@@', '|$$$'
SEPS = CODE_SEP, ARGV_SEP, STDIN_SEP = '~~~|~~~', '@@@|@@@', '$$$|$$$'
LANGUAGE_DIVIDER, COMMENT_PREFIX = '|', '!'

ALL_KEY = 'all'
LANGUAGES_KEY = 'languages'
STRIP_BLANK_LINES_KEY = 'strip_blank_lines'
FILE_PLACEHOLDER, ARGV_PLACEHOLDER = '$file', '$argv'
FILE_MISSING_APPEND = f' {FILE_PLACEHOLDER}'
ARGV_MISSING_APPEND = f' {ARGV_PLACEHOLDER}'

DEFAULT_LANGUAGES_JSON = 'default_languages.json'
BACKUP_LANGUAGES_JSON = {
    ALL_KEY: "All",
    LANGUAGES_KEY: {
        "Python": "python"
    },
    STRIP_BLANK_LINES_KEY: True
}


def removeprefix(string: str, prefix: str) -> str:
    return string[len(prefix):] if string.startswith(prefix) else string


def removesuffix(string: str, suffix: str) -> str:
    return string[:-len(suffix)] if string.endswith(suffix) else string


SectionType = Enum('SectionType', ['CODE', 'ARGV', 'STDIN'])


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
            self.languages = [lang.strip() for lang in header.split(LANGUAGE_DIVIDER)]

    def __str__(self) -> str:
        return self.header

    def __repr__(self) -> str:
        return f"{'//' if self.commented else ''}{self.type.name} " \
               f"{'SEP' if self.is_sep else self.languages} line {self.line_number}"

    @staticmethod
    def line_is_header(line: str) -> bool:
        line = removeprefix(line.rstrip(), COMMENT_PREFIX)
        return line in SEPS or \
            any(line.startswith(start) and line.endswith(end) for start, end in zip(STARTS, ENDS))


def load_languages_json(languages_json: str) -> Any:
    try:
        with open(languages_json) as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return BACKUP_LANGUAGES_JSON


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


def runmany(manyfile: str,
            languages_json: str = DEFAULT_LANGUAGES_JSON) -> None:
    languages_json = load_languages_json(languages_json)
    with open(manyfile) as file:
        for section in section_iterator(file):
            # print(section)
            print(repr(section))


if __name__ == "__main__":
    runmany('test.many')
    print('DONE')

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
