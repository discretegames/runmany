import re
import enum
from typing import List, Optional, Tuple, Generator, Union, TextIO, cast

from runmany.settings import Settings
from runmany.util import removeprefix, removesuffix, print_err


class Syntax:
    COLON = ':'
    STDIN_KEYWORD = "Stdin"
    ARGV_KEYWORD = "Argv"
    ALSO_KEYWORD = "Also{Sec"
    EXIT_KEYWORD = "Exit."
    HEADER_PATTERN = "^( [^,:], "

    LANGUAGE_DIVIDER = ','
    DISABLE_PREFIX = '!'
    INLINE_COMMENT = '%'
    TAB_INDENT = '\t'
    SPACE_INDENT = '    '
    # todo block comments?


class SectionType(enum.Enum):
    CODE = enum.auto()
    ARGV = enum.auto()
    STDIN = enum.auto()


class Section:
    def __init__(self, header: str, content: str, line_number: int, settings: Settings) -> None:
        self.type, start, end = self.get_type_start_end(self.header)
        self.disabled = self.header.startswith(Syntax.DISABLE_PREFIX)

        raw_header = removeprefix(self.header, Syntax.DISABLE_PREFIX)
        self.is_sep = raw_header in Syntax.SEPS
        self.has_content = bool(content.strip('\r\n'))
        self.content = self.strip_content(content, self.type)
        self.line_number = line_number

        self.languages = []
        if not self.is_sep:
            raw_header = removesuffix(removeprefix(raw_header, start), end)
            for language in raw_header.split(Syntax.LANGUAGE_DIVIDER):
                try:
                    self.languages.extend(settings.unpack(language))
                except KeyError:
                    if not self.disabled:
                        print_err(f'Language "{language.strip()}" in section header at line {self.line_number}'
                                  ' not found in json. Skipping language.')

    @staticmethod
    def get_type_start_end(header: str) -> Tuple[SectionType, str, str]:
        if header == Syntax.ARGV_SEP or header.startswith(Syntax.ARGV_START):
            return SectionType.ARGV, Syntax.ARGV_START, Syntax.ARGV_END
        elif header == Syntax.STDIN_SEP or header.startswith(Syntax.STDIN_START):
            return SectionType.STDIN, Syntax.STDIN_START, Syntax.STDIN_END
        else:
            return SectionType.CODE, Syntax.CODE_START, Syntax.CODE_END

    @staticmethod
    def strip_content(content: str, section_type: SectionType) -> str:
        if section_type is SectionType.ARGV:
            return content.strip('\r\n')  # Always strip argv.
        elif section_type is SectionType.STDIN:
            return content.strip('\r\n') + '\n'  # Always strip stdin except trailing newline.
        else:
            return content  # Never strip code.


def line_is_exit(line: str) -> bool:
    return line.startswith(Syntax.EXIT_KEYWORD)


def line_is_comment(line: str) -> bool:
    return line.startswith(Syntax.INLINE_COMMENT)


def line_is_indented(line: str) -> bool:
    return line.startswith(Syntax.TAB_INDENT) or line.startswith(Syntax.SPACE_INDENT)


def try_parse_header(line: str) -> Optional[Tuple[str, str]]:
    return 'a', 'b'  # TODO be sure to handle disabled header
    pass


def section_iterator(file: TextIO) -> Generator[Union[str, None, Section], Settings, None]:
    def current_section() -> Section:
        return Section(cast(str, header), ''.join(section_content), header_line_number, settings)

    header: Optional[str] = None
    header_line_number = 0
    section_content: List[str] = []
    for line_number, line in enumerate(file, 1):
        if line_is_exit(line):
            break
        if line_is_comment(line):
            continue
        if line_is_indented(line):
            line = removeprefix(line, Syntax.TAB_INDENT if line.startswith(Syntax.TAB_INDENT) else Syntax.SPACE_INDENT)
            section_content.append(line)
            continue

        maybe_header = try_parse_header(line)
        if maybe_header is None:
            print_err(f'Skipping line {line_number} "{line}" as it is not a section header and not indented.')
            continue

        if header is None:
            settings = yield ''.join(section_content)  # Yield JSON string at top. Only happens once.
            yield None  # Extra yield needed to send back to the send from run_iterator.
        else:
            yield current_section()

        header, top_line = maybe_header
        header_line_number = line_number
        section_content.clear()
        section_content.append(top_line)

    if header is None:  # Deal with last section header.
        yield ''.join(section_content)
        yield None
    else:
        yield current_section()
