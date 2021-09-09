import re
import enum
from typing import List, Optional, Tuple, Generator, Union, TextIO, cast

from dataclasses import dataclass

from runmany.settings import Settings
from runmany.util import removeprefix, removesuffix, print_err


class Syntax:
    ARGV_ALL = "Argv"
    ARGV_FOR = f"{ARGV_ALL} for"
    STDIN_ALL = "Stdin"
    STDIN_FOR = f"{STDIN_ALL} for"
    ALSO = "Also"
    DISABLER = '!'
    HEADER_END = ':'
    SEPARATOR = ','
    COMMENT = '%'
    EXIT = "Exit."
    TAB_INDENT = '\t'
    SPACE_INDENT = '    '
    PATTERN1 = f'(?=\S)((?:{DISABLER})?)((?:{ARGV_ALL})|(?:{STDIN_ALL})|(?:{ALSO}))\s*(?:{HEADER_END})\s*(.*)'
    PATTERN2 = f'(?=\S)((?:{DISABLER})?)((?:{ARGV_FOR}\s)|(?:{STDIN_FOR}\s)|)([^{HEADER_END}]*?)(?:{HEADER_END})\s*(.*)'
    # todo block comments?


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
    line_number: int
    languages: List[str]
    content: str = ''

    @staticmethod
    def try_start_section(line: str, line_number: int, settings: Settings) -> Optional[Tuple['Section', str]]:
        if Syntax.HEADER_END not in line:
            return None

        match = re.fullmatch(Syntax.PATTERN1, line)
        if match:  # Matched "Argv:", "Stdin:", or "Also:" style header.
            disabler, keyword, top_line = match.groups()
            if keyword == Syntax.ALSO:
                section_type = SectionType.UNKNOWN
                is_also = True
                languages = []
            else:
                section_type = SectionType.ARGV if keyword == Syntax.ARGV_ALL else SectionType.STDIN
                is_also = False
                languages = settings.all_languages()
            return Section(section_type, bool(disabler), is_also, line_number, languages), top_line

        match = re.fullmatch(Syntax.PATTERN2, line)
        if match:  # Matched "Argv for Lang1, Lang2:" or "Stdin for Lang1, Lang2:" style header.
            disabler, keyword, langs, top_line = match.groups()
            languages = [language.strip() for language in langs.split(Syntax.SEPARATOR)]
            if not keyword:
                section_type = SectionType.CODE
            else:
                section_type = SectionType.ARGV if keyword.rstrip() == Syntax.ARGV_FOR else SectionType.STDIN
            return Section(section_type, bool(disabler), False, line_number, languages), top_line

        return None

    def set_content(self, content: str) -> None:
        if self.type is SectionType.ARGV:
            self.content = content.strip('\r\n')  # Always strip argv.
        elif self.type is SectionType.STDIN:
            self.content = content.strip('\r\n') + '\n'  # Always strip stdin except trailing newline.
        else:
            self.content = content  # Never strip code.
        self.has_content = bool(content.strip('\r\n'))  # todo combine with .content later

    def finish_section(self, lead_section_type: SectionType, content: str) -> SectionType:
        if self.type is SectionType.UNKNOWN:
            self.type = lead_section_type
        self.set_content(content)
        return self.type


def line_is_exit(line: str) -> bool:
    return line.startswith(Syntax.EXIT)


def line_is_comment(line: str) -> bool:
    return line.startswith(Syntax.COMMENT)


def line_is_indented(line: str) -> bool:
    return line.startswith(Syntax.TAB_INDENT) or line.startswith(Syntax.SPACE_INDENT)


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
        if line_is_indented(line):
            line = removeprefix(line, Syntax.TAB_INDENT if line.startswith(Syntax.TAB_INDENT) else Syntax.SPACE_INDENT)
            content.append(line)
            continue

        # TODO we need settings for all langs but don't yet know what it is, hmm
        next_section = Section.try_start_section(line, line_number, settings)
        if next_section is None:
            print_err(f'Skipping line {line_number} "{line}" as it is not a section header and not indented.')
            continue

        if section is None:
            settings = yield ''.join(content)  # Yield JSON string at top. Only happens once.
            yield None  # Extra yield needed to send back to the send from run_iterator.
        else:
            lead_section_type = section.finish_section(lead_section_type, ''.join(content))
            yield section

        section, top_line = next_section
        content.clear()
        content.append(top_line)

    if section is None:  # Deal with last section header.
        yield ''.join(content)
        yield None
    else:
        section.finish_section(lead_section_type, ''.join(content))
        yield section
