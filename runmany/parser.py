import re
import enum
from typing import List, Optional, Tuple, Generator, Union, TextIO, cast

from runmany.settings import Settings
from runmany.util import removeprefix, removesuffix, print_err


class Syntax:
    ARGV_KEYWORD = "Argv for"  # todo ensure whitespace after for
    STDIN_KEYWORD = "Stdin for"
    ALSO_KEYWORD = "Also"
    EXIT_KEYWORD = "Exit."
    HEADER_SUFFIX = ':'

    LANGUAGE_DIVIDER = ','
    DISABLE_PREFIX = '!'
    INLINE_COMMENT = '%'
    TAB_INDENT = '\t'
    SPACE_INDENT = '    '
    # todo block comments?


class SectionType(enum.Enum):  # todo rename back to section type
    CODE = enum.auto()
    ARGV = enum.auto()
    STDIN = enum.auto()
    UNKNOWN = enum.auto()


class Section:
    def __init__(
            self, header: str, header_type: SectionType, line_number: int, content: str, settings: Settings) -> None:
        self.header = header
        self.header_type = header_type
        self.line_number = line_number

        self.is_disabled = self.header.startswith(Syntax.DISABLE_PREFIX)
        self.is_also = get_header_type(self.header) is SectionType.UNKNOWN
        self.has_content = bool(content.strip('\r\n'))  # todo combine with .content later, need to change set_content
        self.init_content(content)
        self.init_languages(settings)

        self.languages = get_header_languages(header, settings)
        if self.is_also:
            return

        raw_header = get_plain_header(self.header)
        if not self.is_also:
            raw_header = removesuffix(removeprefix(raw_header, start), end)
            for language in raw_header.split(Syntax.LANGUAGE_DIVIDER):
                try:
                    self.languages.extend(settings.unpack(language))  # todo empty is all now
                except KeyError:
                    if not self.is_disabled:
                        print_err(f'Language "{language.strip()}" in section header at line {self.line_number}'
                                  ' not found in json. Skipping language.')

    def init_content(self, content: str) -> None:
        if self.header_type is SectionType.ARGV:
            self.content = content.strip('\r\n')  # Always strip argv.
        elif self.header_type is SectionType.STDIN:
            self.content = content.strip('\r\n') + '\n'  # Always strip stdin except trailing newline.
        else:
            self.content = content  # Never strip code.

    def init_languages(self, settings: Settings) -> None:
        header = get_plain_header(self.header)
        pass

    @staticmethod
    def try_start_section(line: str, settings: Settings) -> Optional[Tuple['Section', str]]:
        pass

    def set_content(self, content: str):
        # todo
        pass

    def update_type(self, section_type: SectionType) -> SectionType:
        if self.type is SectionType.UNKNOWN:
            self.type = section_type
        return self.type


def line_is_exit(line: str) -> bool:
    return line.startswith(Syntax.EXIT_KEYWORD)


def line_is_comment(line: str) -> bool:
    return line.startswith(Syntax.INLINE_COMMENT)


def line_is_indented(line: str) -> bool:
    return line.startswith(Syntax.TAB_INDENT) or line.startswith(Syntax.SPACE_INDENT)

# todo remove
# def get_plain_header(header: str) -> str:
#     return removeprefix(header, Syntax.DISABLE_PREFIX)


# def get_header_type(header: str, last_header_type: SectionType = SectionType.UNKNOWN) -> SectionType:
#     header = get_plain_header(header)
#     if header.startswith(Syntax.ALSO_KEYWORD + Syntax.HEADER_SUFFIX):
#         return last_header_type
#     if header.startswith(Syntax.ARGV_KEYWORD):
#         return SectionType.ARGV
#     if header.startswith(Syntax.STDIN_KEYWORD):
#         return SectionType.STDIN
#     return SectionType.CODE


def section_iterator(file: TextIO) -> Generator[Union[str, None, Section], Settings, None]:
    section: Optional[Section] = None
    lead_section_type = SectionType.UNKNOWN
    content: List[str] = []

    def finish_section() -> Section:
        nonlocal lead_section_type
        lead_section_type = section.update_type(lead_section_type)
        section.set_content(''.join(content))
        return section

    for line_number, line in enumerate(file, 1):
        if line_is_exit(line):
            break
        if line_is_comment(line):
            continue
        if line_is_indented(line):
            line = removeprefix(line, Syntax.TAB_INDENT if line.startswith(Syntax.TAB_INDENT) else Syntax.SPACE_INDENT)
            content.append(line)
            continue

        next_section = Section.try_start_section(line, settings)
        if next_section is None:
            print_err(f'Skipping line {line_number} "{line}" as it is not a section header and not indented.')
            continue

        if section is None:
            settings = yield ''.join(content)  # Yield JSON string at top. Only happens once.
            yield None  # Extra yield needed to send back to the send from run_iterator.
        else:
            yield finish_section()

        section, top_line = next_section
        content.clear()
        content.append(top_line)

    if section is None:  # Deal with last section header.
        yield ''.join(content)
        yield None
    else:
        yield finish_section()
