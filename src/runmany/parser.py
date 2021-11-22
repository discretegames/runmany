"""RunMany parser module. Handles parsing .many files."""

import os
import re
from pprint import pformat
from typing import Iterator, List, Optional, Type, cast
from abc import ABC, abstractmethod
from runmany.settings import Settings
from runmany.util import print_err, convert_none_false_true


class Syntax(ABC):  # pylint: disable=too-few-public-methods
    SETTINGS = 'Settings'
    ARGV = 'Argv'
    STDIN = 'Stdin'
    FOR = 'for'
    ALSO = 'Also'
    END = 'End.'
    START = 'START:'
    STOP = 'STOP.'
    DISABLER = '!'
    SOLOER = '@'
    SECTION_DISABLER = '!!'
    SECTION_SOLOER = '@@'
    SEPARATOR = ','
    FINISHER = ':'
    LEADING_COMMENT = '%'
    INLINE_COMMENT = '%%%'
    TAB_INDENT = '\t'
    SPACE = ' '
    SPACE_INDENT_LENGTH = 4
    SPACE_INDENT = SPACE * SPACE_INDENT_LENGTH

    UNINDENT_PATTERN = f'^(?:{TAB_INDENT}|{SPACE}{{1,{SPACE_INDENT_LENGTH}}})'
    HEADER_START = f'^(?=\\S)({SECTION_DISABLER}|{SECTION_SOLOER}|)?({DISABLER}|{SOLOER}|)?\\s*'
    HEADER_END = '\\s*:'
    SETTINGS_HEADER = HEADER_START + f'({SETTINGS})' + HEADER_END
    ARGV_HEADER = HEADER_START + f'{ARGV}(?:\\s+{FOR}\\b([^:]*))?' + HEADER_END
    STDIN_HEADER = HEADER_START + f'{STDIN}(?:\\s+{FOR}\\b([^:]*))?' + HEADER_END
    CODE_HEADER = f'{HEADER_START}([^:]*){HEADER_END}'
    ALSO_HEADER = f'^(?=\\S)({DISABLER}|{SOLOER}|)?\\s*{ALSO}' + HEADER_END


class Snippet:
    def __init__(self, parser: 'Parser', first_line: int, last_line: int, sd_match: Optional[str]):
        self.parser = parser
        self.first_line = first_line
        self.last_line = last_line
        if sd_match is None:
            sd_match = cast(re.Match[str], self.get_also_header_match(parser.lines[first_line])).group(1)
        self.is_disabled = sd_match == Syntax.DISABLER
        self.is_solo = sd_match == Syntax.SOLOER

    def content(self, top_line: int, bottom_line: int, unindent: bool, strip: bool, newline: str) -> Optional[str]:
        lines = self.parser.lines.copy()
        header = lines[self.first_line]
        lines[self.first_line] = Syntax.TAB_INDENT + header[header.index(Syntax.FINISHER) + 1:].lstrip()
        for i, line in enumerate(lines):
            if i < self.first_line or i > self.last_line:
                lines[i] = ''
            elif unindent:
                lines[i] = re.sub(Syntax.UNINDENT_PATTERN, '', line)
        lines = lines[top_line:bottom_line + 1]
        if strip:
            lines = [line for line in lines if line.strip()]
        result = newline.join(lines)
        if self.parser.settings.ignore_blanks and not result.strip():
            return None
        return result

    @staticmethod
    def get_also_header_match(line: str) -> Optional[re.Match[str]]:
        return re.match(Syntax.ALSO_HEADER, line)

    @staticmethod
    def line_is_also_header(line: str) -> bool:
        return bool(Snippet.get_also_header_match(line))

    @staticmethod
    def line_is_indented(line: str) -> bool:
        return line.startswith(Syntax.TAB_INDENT) or line.startswith(Syntax.SPACE_INDENT) or not line.rstrip()

    def __str__(self) -> str:
        return pformat(self.parser.lines[self.first_line:self.last_line + 1])

    def __repr__(self) -> str:
        return str(self)


class Section(ABC):  # pylint: disable=too-many-instance-attributes
    def __init__(self, parser: 'Parser', first_line: int, last_line: int):
        self.parser = parser
        self.first_line = first_line
        self.last_line = last_line
        groups = cast(re.Match[str], self.get_header_match(self.parser.lines[first_line])).groups()
        self.is_disabled = groups[0] == Syntax.SECTION_DISABLER
        self.is_solo = groups[0] == Syntax.SECTION_SOLOER
        if cast(Optional[str], groups[2]) is None:
            self.language_names: List[str] = []
        else:  # All sections except Settings use language_names. It'll be an empty list for Argv/Stdins without "for".
            self.language_names = [name.strip() for name in groups[2].split(Syntax.SEPARATOR)]
        self.make_snippets(groups[1])  # groups[1] is the first snippet's solo/disabled match
        self.has_solo_snippets = any(snippet.is_solo for snippet in self.snippets)

    def make_snippets(self, first_sd_match: str) -> None:
        def add_snippet() -> None:
            sd_match = None if self.snippets else first_sd_match
            self.snippets.append(Snippet(self.parser, snippet_first_line, i - 1, sd_match))
        self.snippets: List[Snippet] = []
        snippet_first_line = self.first_line
        i = snippet_first_line + 1
        while i <= self.last_line:
            line = self.parser.lines[i]
            if Snippet.line_is_also_header(line):
                add_snippet()
                snippet_first_line = i
            elif not Snippet.line_is_indented(line):
                self.parser.lines[i] = ''
                print_err(f'Skipping invalid unindented line {i} "{line}".')
            i += 1
        add_snippet()

    @staticmethod
    def try_get_section_type(line: str) -> Optional[Type['Section']]:
        if SettingsSection.get_header_match(line):
            return SettingsSection
        if ArgvSection.get_header_match(line):
            return ArgvSection
        if StdinSection.get_header_match(line):
            return StdinSection
        if not Snippet.line_is_also_header(line) and CodeSection.get_header_match(line):
            return CodeSection
        return None

    @staticmethod
    @abstractmethod
    def get_header_match(line: str) -> Optional[re.Match[str]]:
        pass

    @abstractmethod
    def run(self) -> None:
        pass

    def __iter__(self) -> Iterator[Snippet]:
        snippets = self.snippets
        if not self.parser.settings.ignore_disabled:
            snippets = [snippet for snippet in snippets if not snippet.is_disabled]
        if not self.parser.settings.ignore_solos and self.has_solo_snippets:
            snippets = [snippet for snippet in snippets if snippet.is_solo]
        return iter(snippets)

    def __str__(self) -> str:
        return pformat((self.__class__.__name__, self.first_line, self.last_line, self.snippets))

    def __repr__(self) -> str:
        return str(self)


class SettingsSection(Section):
    @staticmethod
    def get_header_match(line: str) -> Optional[re.Match[str]]:
        return re.match(Syntax.SETTINGS_HEADER, line)

    def run(self) -> None:
        for snippet in self:
            content = snippet.content(0, snippet.last_line, False, False, '\n')
            if content is not None:
                self.parser.settings.update_with_json(content)


class ArgvSection(Section):
    @staticmethod
    def get_header_match(line: str) -> Optional[re.Match[str]]:
        return re.match(Syntax.ARGV_HEADER, line)

    def run(self) -> None:
        pass


class StdinSection(Section):
    @staticmethod
    def get_header_match(line: str) -> Optional[re.Match[str]]:
        return re.match(Syntax.STDIN_HEADER, line)

    def run(self) -> None:
        return


class CodeSection(Section):
    @staticmethod
    def get_header_match(line: str) -> Optional[re.Match[str]]:
        return re.match(Syntax.CODE_HEADER, line)

    def run(self) -> None:
        for language_name in self.language_names:
            language = self.parser.settings[language_name]
            for snippet in self:
                strip_code = convert_none_false_true(self.parser.settings.strip_code, "smart", "yes", "no")
                content: Optional[str] = None
                newline: str = language.replace_newline if language.replace_newline is not None else os.linesep
                if strip_code is None:
                    content = snippet.content(0, snippet.last_line, True, False, newline)
                elif strip_code is False:
                    content = snippet.content(0, len(self.parser.lines) - 1, False, False, newline)
                elif strip_code is True:
                    content = snippet.content(snippet.first_line, snippet.last_line, True, True, newline)
                if content and language.replace_tab is not None:
                    content = content.replace('\t', cast(str, language.replace_tab))

                print(language, repr(content))


class Parser:
    def __init__(self, manyfile: str, settings: Settings) -> None:
        self.settings = settings
        self.lines = manyfile.splitlines()
        self.first_line = self.get_first_line()
        self.last_line = self.get_last_line()
        self.clean_lines()
        self.make_sections()
        self.has_solo_sections = any(section.is_solo for section in self.sections)
        self.has_solo_snippets = any(section.has_solo_snippets for section in self.sections)

    def get_first_line(self) -> int:
        for i in range(len(self.lines) - 1, -1, -1):
            if self.lines[i].rstrip().startswith(Syntax.START):
                return i + 1
        return 0

    def get_last_line(self) -> int:
        for i, line in enumerate(self.lines):
            if line.rstrip().startswith(Syntax.STOP):
                return i - 1
        return len(self.lines) - 1

    def clean_lines(self) -> None:
        for i, line in enumerate(self.lines):
            if i < self.first_line or i > self.last_line or line.startswith(Syntax.LEADING_COMMENT):
                self.lines[i] = ''
            elif not self.settings.ignore_comments:
                index = line.find(Syntax.INLINE_COMMENT)
                if index >= 0:
                    self.lines[i] = line[:index]

    def make_sections(self) -> None:
        self.sections: List[Section] = []
        i, in_section = self.first_line, False
        while i <= self.last_line:
            line = self.lines[i]
            if not in_section:
                tried_section_type = Section.try_get_section_type(line)
                if tried_section_type:
                    in_section = True
                    section_first_line = i
                    section_type = tried_section_type
            elif line.rstrip().startswith(Syntax.END) or Section.try_get_section_type(line):
                in_section = False
                i -= 1
                self.sections.append(section_type(self, section_first_line, i))
            i += 1
        if in_section:
            self.sections.append(section_type(self, section_first_line, self.last_line))

    def __iter__(self) -> Iterator[Section]:
        sections = self.sections
        if not self.settings.ignore_disabled:
            sections = [section for section in sections if not section.is_disabled]
        if not self.settings.ignore_solos:
            if self.has_solo_sections:
                sections = [section for section in sections if section.is_solo]
            if self.has_solo_snippets:
                sections = [section for section in sections if section.has_solo_snippets]
        return iter(sections)

    def __str__(self) -> str:
        return pformat(self.sections)

    def __repr__(self) -> str:
        return str(self)
