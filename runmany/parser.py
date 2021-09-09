import re
import enum
from typing import List, Optional, Tuple, Generator, Union, TextIO, cast

from runmany.settings import Settings
from runmany.util import removeprefix, removesuffix, print_err


class Syntax:
    ARGV_KEYWORD = "Argv"
    STDIN_KEYWORD = "Stdin"
    ALSO_KEYWORD = "Also"
    EXIT_KEYWORD = "Exit."
    HEADER_SUFFIX = ':'
    HEADER_PATTERN = "^( [^,:], "  # todo

    LANGUAGE_DIVIDER = ','
    DISABLE_PREFIX = '!'
    INLINE_COMMENT = '%'
    TAB_INDENT = '\t'
    SPACE_INDENT = '    '
    # todo block comments?


# todo
class HeaderType(enum.Enum):
    CODE = enum.auto()
    ARGV = enum.auto()
    STDIN = enum.auto()
    UNKNOWN = enum.auto()


class Section:
    def __init__(
            self, header: str, header_type: HeaderType, line_number: int, content: str, settings: Settings) -> None:
        self.header = header
        self.header_type = header_type
        self.line_number = line_number

        self.is_disabled = self.header.startswith(Syntax.DISABLE_PREFIX)
        self.is_also = get_header_type(self.header) is HeaderType.UNKNOWN
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
        if self.header_type is HeaderType.ARGV:
            self.content = content.strip('\r\n')  # Always strip argv.
        elif self.header_type is HeaderType.STDIN:
            self.content = content.strip('\r\n') + '\n'  # Always strip stdin except trailing newline.
        else:
            self.content = content  # Never strip code.

    def init_languages(self, settings: Settings) -> None:
        header = get_plain_header(self.header)
        pass


def line_is_exit(line: str) -> bool:
    return line.startswith(Syntax.EXIT_KEYWORD)


def line_is_comment(line: str) -> bool:
    return line.startswith(Syntax.INLINE_COMMENT)


def line_is_indented(line: str) -> bool:
    return line.startswith(Syntax.TAB_INDENT) or line.startswith(Syntax.SPACE_INDENT)


def try_parse_header(line: str) -> Optional[Tuple[str, str]]:
    return 'a', 'b'  # TODO be sure to handle disabled header


def get_plain_header(header: str) -> str:
    return removeprefix(header, Syntax.DISABLE_PREFIX)


def get_header_type(header: str, last_header_type: HeaderType = HeaderType.UNKNOWN) -> HeaderType:
    header = get_plain_header(header)
    if header.startswith(Syntax.ALSO_KEYWORD + Syntax.HEADER_SUFFIX):
        return last_header_type
    if header.startswith(Syntax.ARGV_KEYWORD):
        return HeaderType.ARGV
    if header.startswith(Syntax.STDIN_KEYWORD):
        return HeaderType.STDIN
    return HeaderType.CODE


def section_iterator(file: TextIO) -> Generator[Union[str, None, Section], Settings, None]:
    header: Optional[str] = None
    header_type = HeaderType.UNKNOWN
    header_line_number = 0
    content: List[str] = []

    def current_section() -> Section:
        nonlocal header_type
        header_type = get_header_type(cast(str, header), header_type)
        return Section(cast(str, header), header_type, header_line_number, ''.join(content), settings)

    for line_number, line in enumerate(file, 1):
        if line_is_exit(line):
            break
        if line_is_comment(line):
            continue
        if line_is_indented(line):
            line = removeprefix(line, Syntax.TAB_INDENT if line.startswith(Syntax.TAB_INDENT) else Syntax.SPACE_INDENT)
            content.append(line)
            continue

        maybe_header = try_parse_header(line)
        if maybe_header is None:
            print_err(f'Skipping line {line_number} "{line}" as it is not a section header and not indented.')
            continue

        if header is None:
            settings = yield ''.join(content)  # Yield JSON string at top. Only happens once.
            yield None  # Extra yield needed to send back to the send from run_iterator.
        else:
            yield current_section()

        header, top_line = maybe_header
        header_line_number = line_number
        content.clear()
        content.append(top_line)

    if header is None:  # Deal with last section header.
        yield ''.join(content)
        yield None
    else:
        yield current_section()
