
"""todo"""

import re
import os
from typing import Iterator, List, Optional, Type, cast
from abc import ABC, abstractmethod
from runmany.settings import Settings

# pylint: disable=too-few-public-methods


class Syntax(ABC):
    SETTINGS = 'Settings'
    ARGV = 'Argv'
    STDIN = 'Stdin'
    FOR = 'for'
    ALSO = 'Also'
    END = 'End.'
    DISABLER = '!'
    SECTION_DISABLER = 2 * DISABLER
    SOLOER = '@'
    SECTION_SOLOER = 2 * SOLOER
    HEADER_END = ':'
    SEPARATOR = ','
    COMMENT = '%'
    INLINE_COMMENT = '%%%'
    START = 'START:'
    STOP = 'STOP.'
    TAB_INDENT = '\t'
    SPACE = ' '
    SPACE_INDENT_LENGTH = 4
    SPACE_INDENT = SPACE * SPACE_INDENT_LENGTH

    HEADER_START, HEADER_END = '^(?=\\S)(!!|@@)?(!|@)?\\s*', '\\s*:'
    SETTINGS_HEADER = HEADER_START + '(Settings)' + HEADER_END
    ARGV_HEADER = HEADER_START + 'Argv(?:\\s+for\\b([^:]*))?' + HEADER_END
    STDIN_HEADER = HEADER_START + 'Stdin(?:\\s+for\\b([^:]*))?' + HEADER_END
    CODE_HEADER = HEADER_START + '([^:]*)' + HEADER_END
    ALSO_HEADER = '^(?=\\S)(!|@)?\\s*Also' + HEADER_END


class Snippet:
    def __init__(self, parser: 'Parser', first_line: int, last_line: int):
        self.parser = parser
        self.first_line = first_line
        self.last_line = last_line


class Section(ABC):
    def __init__(self, parser: 'Parser', first_line: int, last_line: int):
        self.parser = parser
        self.first_line = first_line
        self.last_line = last_line
        matches = cast(re.Match[str], self.get_header_match(self.parser.lines[first_line])).groups()
        self.is_disabled = matches[0] == Syntax.SECTION_DISABLER
        self.is_solo = matches[0] == Syntax.SECTION_SOLOER
        self.header_arg = matches[2]
        # self.set_snippets()
        # todo solos list of indexes

    # def set_snippets(self) -> None:
    #     self.snippets: List[Snippet] = []

    #     i = self.first_line + 1
    #     while i <= self.last_line:
    #         # if line is Also: then make snippet from

    #     snippet_firsts: List[int] = []

    # def create_also
    # self.alsos: Also = []
    # todo ignore unindented non also-lines

    # print(match.groups())

    @staticmethod
    def try_get_section_type(line: str) -> Optional[Type['Section']]:
        if SettingsSection.get_header_match(line):
            return SettingsSection
        if ArgvSection.get_header_match(line):
            return ArgvSection
        if StdinSection.get_header_match(line):
            return StdinSection
        if CodeSection.get_header_match(line):
            return CodeSection
        return None

    @staticmethod
    @abstractmethod
    def get_header_match(line: str) -> Optional[re.Match[str]]:
        pass

    @abstractmethod
    def run(self) -> None:
        pass

    def __str__(self) -> str:
        return str((self.__class__.__name__, self.first_line, self.last_line))

    def __repr__(self) -> str:
        return str(self)


class SettingsSection(Section):

    @staticmethod
    def get_header_match(line: str) -> Optional[re.Match[str]]:
        return re.match(Syntax.SETTINGS_HEADER, line)

    def run(self) -> None:
        pass


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
        pass


class CodeSection(Section):
    @staticmethod
    def get_header_match(line: str) -> Optional[re.Match[str]]:
        return re.match(Syntax.CODE_HEADER, line)

    def run(self) -> None:
        pass


class Parser:
    def __init__(self, manyfile: str, settings: Settings) -> None:
        self.settings = settings
        self.lines = manyfile.splitlines()
        self.first_line = self.get_first_line()
        self.last_line = self.get_last_line()
        self.clean_lines()
        self.set_sections()
        self.has_solo_sections = any(section.is_solo for section in self.sections)
        # self.has_solo_snippets = any(section.has_solo_snippets for section in self.sections)

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
            if i < self.first_line or i > self.last_line or line.startswith(Syntax.COMMENT):
                self.lines[i] = ''
            elif not self.settings.ignore_comments:
                index = line.find(Syntax.INLINE_COMMENT)
                if index >= 0:
                    self.lines[i] = line[:index]

    def set_sections(self) -> None:
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
            else:
                if i == self.last_line:
                    self.sections.append(section_type(self, section_first_line, i))
                else:
                    if line.rstrip().startswith(Syntax.END) or Section.try_get_section_type(line):
                        in_section = False
                        i -= 1
                        self.sections.append(section_type(self, section_first_line, i))
            i += 1

    def __iter__(self) -> Iterator[Section]:
        # if not self.settings.ignore_solos:
        #     if self.has_solo_sections:
        #         return iter(section for section in self.sections if section.is_solo)
        #     if self.has_solo_snippets:
        #         return iter(section for section in self.sections if section.has_solo_snippets)
        return iter(self.sections)

    def __str__(self) -> str:
        return os.linesep.join(self.lines)

    def __repr__(self) -> str:
        return str(self.lines)
