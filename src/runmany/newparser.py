
"""todo"""

import re
import os
from typing import List, Optional, Type
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
    SOLOER = '@'
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

    HEADER_START, HEADER_END = '^(?=\\S)(!!|@@)?(!|@)?\\s*', '\\s*:\\s*(.*)$'
    SETTINGS_HEADER = HEADER_START + 'Settings' + HEADER_END
    ARGV_HEADER = HEADER_START + 'Argv(?:\\s+for\\b([^:]*))?' + HEADER_END
    STDIN_HEADER = HEADER_START + 'Stdin(?:\\s+for\\b([^:]*))?' + HEADER_END
    CODE_HEADER = HEADER_START + '([^:]*)' + HEADER_END
    ALSO_HEADER = '^(?=\\S)(!|@)?\\s*Also' + HEADER_END


class Also:
    pass


class Section(ABC):
    def __init__(self, lines: List[str], header_line: int, limit_line: int):
        self.lines = lines
        self.header_line = header_line
        # step through lines until find another header or End. or end of file

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

    # def parse_section(lines: List[str], curr_line: int, last_line: int) -> 'Section':
    #     return Section()

    @staticmethod
    @abstractmethod
    def get_header_match(line: str) -> Optional[re.Match[str]]:
        pass

    @abstractmethod
    def run(self) -> None:
        pass


class SettingsSection(Section):
    def __init__(self, lines: List[str], header_line: int, limit_line: int):
        super().__init__(lines, header_line, limit_line)

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
            elif not self.settings.run_comments:
                index = line.find(Syntax.INLINE_COMMENT)
                if index >= 0:
                    self.lines[i] = line[:index]

    # def get_sections(self) -> List[Section]:
    #     sections: List[Section] = []
    #     i = self.first_line
    #     while i <= self.last_line:
    #         line = self.lines[i]
    #         section_type = Section.try_get_section_type(line)
    #         if section_type:
    #             sections.append(section_type(self.lines, i, self.last_line))
    #             i = sections[-1].final_line
    #         i += 1
    #     return sections

    def get_sections(self) -> List[Section]:
        section_firsts: List[int] = []
        section_lasts: List[int] = []
        section_types: List[Type[Section]] = []
        i, in_section = self.first_line, False
        while i <= self.last_line:
            line = self.lines[i]
            if not in_section:
                section_type = Section.try_get_section_type(line)
                if section_type:
                    in_section = True
                    section_firsts.append(i)
                    section_types.append(section_type)
            else:
                if i == self.last_line:
                    section_lasts.append(i)
                else:
                    if line.rstrip().startswith(Syntax.END) or Section.try_get_section_type(line):
                        in_section = False
                        i -= 1
                        section_lasts.append(i)
            i += 1
        return [st(self.lines, sf, sl) for sf, sl, st in zip(section_firsts, section_lasts, section_types)]

    def __str__(self) -> str:
        return os.linesep.join(self.lines)

    def __repr__(self) -> str:
        return str(self.lines)
