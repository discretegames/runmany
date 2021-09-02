import enum
from typing import Optional, List, Tuple, Iterator, Union, TextIO, cast
from .util import removeprefix, removesuffix, print_err
from .settings import Settings
# todo organize imports in all main files


class Syntax:
    CODE_START = '~~~|'
    CODE_END = '|~~~'
    CODE_SEP = '~~~|~~~'
    ARGV_START = '@@@|'
    ARGV_END = '|@@@'
    ARGV_SEP = '@@@|@@@'
    STDIN_START = '$$$|'
    STDIN_END = '|$$$'
    STDIN_SEP = '$$$|$$$'
    COMMENT_START = '%%%|'
    COMMENT_END = '|%%%'
    EXIT_MARKER = '%%%|%%%'
    LANGUAGE_DIVIDER = '|'
    DISABLE_PREFIX = '!'

    STARTS = CODE_START, ARGV_START, STDIN_START
    ENDS = CODE_END, ARGV_END, STDIN_END
    SEPS = CODE_SEP, ARGV_SEP, STDIN_SEP


class SectionType(enum.Enum):
    CODE = enum.auto()
    ARGV = enum.auto()
    STDIN = enum.auto()


class Section:
    @staticmethod
    def line_is_exit(line: str) -> bool:
        return line.rstrip() == Syntax.EXIT_MARKER

    @staticmethod
    def line_is_comment(line: str) -> bool:
        line = line.rstrip()
        return line == Syntax.DISABLE_PREFIX + Syntax.EXIT_MARKER or line.endswith(Syntax.COMMENT_END) and \
            (line.startswith(Syntax.COMMENT_START) or line.startswith(Syntax.DISABLE_PREFIX + Syntax.COMMENT_START))

    @staticmethod
    def line_is_header(line: str) -> bool:
        line = removeprefix(line.rstrip(), Syntax.DISABLE_PREFIX)
        return line in Syntax.SEPS or \
            any(line.startswith(s) and line.endswith(e) for s, e in zip(Syntax.STARTS, Syntax.ENDS))

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

    def __init__(self, header: str, content: str, settings: Settings, line_number: int) -> None:
        self.header = header.rstrip()
        self.type, start, end = self.get_type_start_end(self.header)
        self.disabled = self.header.startswith(Syntax.DISABLE_PREFIX)

        raw_header = removeprefix(self.header, Syntax.DISABLE_PREFIX)
        self.is_sep = raw_header in (Syntax.CODE_SEP, Syntax.ARGV_SEP, Syntax.STDIN_SEP)
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


def section_iterator(file: TextIO, settings: Settings) -> Iterator[Union[str, Section]]:
    def current_section() -> Section:
        return Section(cast(str, header), ''.join(section_lines), settings, header_line_number)

    header: Optional[str] = None
    header_line_number = 0
    section_lines: List[str] = []
    for line_number, line in enumerate(file, 1):
        if Section.line_is_exit(line):
            break
        if Section.line_is_comment(line):
            continue
        if Section.line_is_header(line):
            if not header:
                yield ''.join(section_lines)  # Yield prologue. Only happens once. # TODO remove prologue stuff
            else:
                yield current_section()
            header = line
            header_line_number = line_number
            section_lines = []
        else:
            section_lines.append(line)

    if header:
        yield current_section()
