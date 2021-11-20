
"""todo"""

import os
from typing import List
from abc import ABC, abstractmethod
from runmany.settings import Settings

# pylint: disable=too-few-public-methods


class Syntax(ABC):
    ARGV = 'Argv'
    STDIN = 'Stdin'
    FOR = 'for'
    ALSO = 'Also'
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


class Also:
    pass


class Section(ABC):
    @abstractmethod
    def run(self) -> None:
        pass

    @staticmethod
    def line_starts_section(line: str) -> bool:
        return line.startswith(Syntax.START)

    @staticmethod
    def parse_section():
        pass


class SettingsSection(Section):
    pass


class ArgvSection(Section):
    pass


class StdinSection(Section):
    pass


class CodeSection(Section):
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

    def get_sections(self) -> List[Section]:
        sections: List[Section] = []
        i = self.first_line
        while i <= self.last_line:
            line = self.lines[i]
            if Section.line_starts_section(line):
                i, section = Section.parse_section(self.lines, i, self.last_line)
                sections.append(section)
        return sections

    def __str__(self) -> str:
        return os.linesep.join(self.lines)

    def __repr__(self) -> str:
        return str(self.lines)
