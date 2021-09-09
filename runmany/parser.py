import re
import enum
from typing import List, Optional, Tuple, Generator, Union, TextIO

from dataclasses import dataclass
from runmany.settings import Settings, normalize
from runmany.util import removeprefix, print_err


class Syntax:
    ARGV = "Argv"
    STDIN = "Stdin"
    FOR = "for"
    ALSO = "Also"
    DISABLER = '!'
    HEADER_END = ':'
    SEPARATOR = ','
    COMMENT = '%'
    EXIT = "Exit."
    TAB_INDENT = '\t'
    SPACE_INDENT = '    '
    PATTERN1 = f'(?=\S)({DISABLER})?((?:{ARGV})|(?:{STDIN})|(?:{ALSO}))\s*(?:{HEADER_END})(.*)'
    PATTERN2 = f'(?=\S)({DISABLER})?(?:({ARGV}|{STDIN})\s+{FOR})?([^{HEADER_END}]*?)(?:{HEADER_END})(.*)'
    # todo block comments?
    # todo tests for varying syntax that follow regex


class SectionType(enum.Enum):
    CODE = enum.auto()
    ARGV = enum.auto()
    STDIN = enum.auto()
    UNKNOWN = enum.auto()


@dataclass
class Section:
    type: SectionType
    is_disabled: bool
    is_also: bool
    is_all: bool
    line_number: int
    languages: List[str]
    content: str = ''

    @staticmethod
    def try_start_section(line: str, line_number: int) -> Optional[Tuple['Section', str]]:
        if Syntax.HEADER_END not in line:
            return None

        match = re.fullmatch(Syntax.PATTERN1, line, re.DOTALL)
        if match:  # Matched "Argv:", "Stdin:", or "Also:" style header.
            disabler, keyword, top_line = match.groups()
            if keyword == Syntax.ALSO:
                section_type = SectionType.UNKNOWN
                is_also = True
            else:
                section_type = SectionType.ARGV if keyword == Syntax.ARGV else SectionType.STDIN
                is_also = False
            return Section(section_type, bool(disabler), is_also, not is_also, line_number, []), top_line

        match = re.fullmatch(Syntax.PATTERN2, line, re.DOTALL)
        if match:  # Matched "Argv for Lang1, Lang2:" or "Stdin for Lang1, Lang2:" style header.
            disabler, keyword, langs, top_line = match.groups()
            languages = [normalize(language) for language in langs.split(Syntax.SEPARATOR)]
            if not keyword:
                section_type = SectionType.CODE
            else:
                section_type = SectionType.ARGV if keyword == Syntax.ARGV else SectionType.STDIN
            return Section(section_type, bool(disabler), False, False, line_number, languages), top_line

        return None

    def set_content(self, content: str) -> None:
        if self.type is SectionType.ARGV:
            self.content = content.strip('\r\n')  # Always strip argv.
        elif self.type is SectionType.STDIN:
            self.content = content.strip('\r\n') + '\n'  # Always strip stdin except trailing newline.
        else:
            self.content = content  # Never strip code.
        self.has_content = bool(content.strip('\r\n'))  # todo combine with .content later

    def finish_section(self, lead_section_type: SectionType, content: str, settings: Settings) -> SectionType:
        if self.type is SectionType.UNKNOWN:
            self.type = lead_section_type
        self.set_content(content)
        if self.is_all:
            self.languages = settings.all_languages()
        return self.type


def line_is_exit(line: str) -> bool:
    return line.startswith(Syntax.EXIT)


def line_is_comment(line: str) -> bool:
    return line.startswith(Syntax.COMMENT)


def line_is_content(line: str) -> bool:
    return line.startswith(Syntax.TAB_INDENT) or line.startswith(Syntax.SPACE_INDENT) or not line.rstrip()


def section_iterator(file: TextIO) -> Generator[Union[str, None, Section], Settings, None]:
    section: Optional[Section] = None
    lead_section_type = SectionType.UNKNOWN
    content: List[str] = []
    settings: Settings

    for line_number, line in enumerate(file, 1):
        if line_is_exit(line):
            break
        if line_is_comment(line):
            continue
        if line_is_content(line):
            line = removeprefix(line, Syntax.TAB_INDENT if line.startswith(Syntax.TAB_INDENT) else Syntax.SPACE_INDENT)
            content.append(line)
            continue

        next_section = Section.try_start_section(line, line_number)
        if not next_section:
            print_err(f'Skipping line {line_number} "{line.strip()}" as it is not a valid section header nor indented.')
            continue

        if section:
            lead_section_type = section.finish_section(lead_section_type, ''.join(content), settings)
            yield section
        else:
            settings = yield ''.join(content)  # Yield JSON string at top. Only happens once.
            yield None  # Extra yield needed to send back to the send from run_iterator.

        section, top_line = next_section
        content.clear()
        content.append(top_line.lstrip())

    if section:  # Deal with last section header.
        section.finish_section(lead_section_type, ''.join(content), settings)
        yield section
    else:
        yield ''.join(content)
        yield None
