"""RunMany parser module. Handles parsing .many files and sending section content to the runner."""

import os
import re
from pprint import pformat
from typing import Iterator, List, Optional, Type, cast
from abc import ABC, abstractmethod
from runmany.settings import Settings, Language
from runmany.runner import Runner
from runmany.util import print_err, convert_smart_yes_no, Content


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

    @staticmethod
    def remove_inline_comment(line: str) -> str:
        return line.split(Syntax.INLINE_COMMENT, 1)[0]

    @staticmethod
    def string_starts_line(string: str, line: str) -> bool:
        return string == Syntax.remove_inline_comment(line).rstrip()


class Snippet:
    def __init__(self, parser: 'Parser', first_line: int, last_line: int, sd_match: Optional[str]):
        self.parser = parser
        self.first_line = first_line
        self.last_line = last_line
        if sd_match is None:
            sd_match = cast('re.Match[str]', self.get_also_header_match(parser.lines[first_line])).group(1)
        self.is_disabled = sd_match == Syntax.DISABLER
        self.is_solo = sd_match == Syntax.SOLOER

    def get_content(self, from_top: bool, strip: bool, unindent: bool, tab: str, newline: str) -> Optional[Content]:
        lines = self.parser.lines[self.first_line: self.last_line + 1]
        lines[0] = Syntax.TAB_INDENT + lines[0][lines[0].index(Syntax.FINISHER) + 1:].lstrip()
        if not self.parser.settings.keep_comments:
            lines = [Syntax.remove_inline_comment(line) for line in lines]
        if unindent:
            lines = [re.sub(Syntax.UNINDENT_PATTERN, '', line) for line in lines]
        prefix_extras = 0
        if strip:
            first, last = 0, len(lines) - 1
            for line in lines:
                if line.strip():
                    break
                first += 1
            for line in reversed(lines):
                if line.strip():
                    break
                last -= 1
            lines = lines[first:last + 1]
            prefix_extras = first
        text = newline.join(lines).replace('\t', tab)
        if not self.parser.settings.run_blanks and not text.strip():
            return None
        prefix_lines = prefix_extras + self.first_line if from_top else 0
        return Content(text, self.first_line, prefix_lines, newline)

    @staticmethod
    def get_also_header_match(line: str) -> Optional['re.Match[str]']:
        return re.match(Syntax.ALSO_HEADER, line)

    @staticmethod
    def line_is_also_header(line: str) -> bool:
        return bool(Snippet.get_also_header_match(line))

    @staticmethod
    def line_is_indented(line: str) -> bool:
        return line.startswith(Syntax.TAB_INDENT) or line.startswith(Syntax.SPACE_INDENT) or not line.rstrip()

    def __str__(self) -> str:
        return pformat(self.parser.lines[self.first_line:self.last_line + 1])  # pragma: no cover

    def __repr__(self) -> str:
        return str(self)  # pragma: no cover


class Section(ABC):
    def __init__(self, parser: 'Parser', first_line: int, last_line: int):
        self.parser = parser
        self.first_line = first_line
        self.last_line = last_line

        groups = cast('re.Match[str]', self.get_header_match(self.parser.lines[first_line])).groups()
        self.is_disabled = groups[0] == Syntax.SECTION_DISABLER
        self.is_solo = groups[0] == Syntax.SECTION_SOLOER
        if cast(Optional[str], groups[2]) is None:
            self.raw_language_names: List[str] = []
        else:  # All sections except Settings use language names. It'll be an empty list for Argv/Stdins without "for".
            self.raw_language_names = groups[2].split(Syntax.SEPARATOR)
        self.language_names = [Language.normalize(name) for name in self.raw_language_names]
        self.make_snippets(groups[1])  # groups[1] is the first snippet's (not section) solo/disabled match

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
                print_err(f'Skipping invalid unindented line {i + 1} "{line}".')
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
    def get_header_match(line: str) -> Optional['re.Match[str]']:
        pass  # pragma: no cover

    @abstractmethod
    def run(self, directory: str) -> None:
        pass  # pragma: no cover

    def __iter__(self) -> Iterator[Snippet]:
        enabled_snippets = [snippet for snippet in self.snippets if not snippet.is_disabled]
        solo_snippets = [snippet for snippet in enabled_snippets if snippet.is_solo]
        return iter(solo_snippets or enabled_snippets)

    def __str__(self) -> str:
        return pformat((self.__class__.__name__, self.first_line, self.last_line, self.snippets))  # pragma: no cover

    def __repr__(self) -> str:
        return str(self)  # pragma: no cover


class SettingsSection(Section):
    @staticmethod
    def get_header_match(line: str) -> Optional['re.Match[str]']:
        return re.match(Syntax.SETTINGS_HEADER, line)

    def run(self, _: str) -> None:
        for snippet in self:
            content = snippet.get_content(True, False, False, '\t', '\n')
            if content is not None:
                self.parser.settings.update_with_json(content.prefixed_text)


class ArgvSection(Section):
    @staticmethod
    def get_header_match(line: str) -> Optional['re.Match[str]']:
        return re.match(Syntax.ARGV_HEADER, line)

    def get_content(self, snippet: Snippet) -> Optional[Content]:
        settings = self.parser.settings
        content: Optional[Content] = None
        strip = convert_smart_yes_no(settings.strip_argv)
        newline: str = settings.newline if settings.newline is not None else os.linesep
        tab: str = settings.tab if settings.tab is not None else '\t'

        if strip is None:
            content = snippet.get_content(False, True, True, tab, newline)
            if content:
                content.text = ' '.join(line.strip() for line in content.text.split(newline))
        elif strip:
            content = snippet.get_content(False, True, True, tab, newline)
            if content:
                content.text = content.text.strip()
        else:
            content = snippet.get_content(False, False, True, tab, newline)
        return content

    def run(self, _: str) -> None:
        argvs: List[Content] = []
        for snippet in self:
            argv = self.get_content(snippet)
            if argv:
                argvs.append(argv)
        for language_name in self.language_names or self.parser.settings.computed_languages():
            self.parser.runner.set_argvs(language_name, argvs)


class StdinSection(Section):
    @staticmethod
    def get_header_match(line: str) -> Optional['re.Match[str]']:
        return re.match(Syntax.STDIN_HEADER, line)

    def get_content(self, snippet: Snippet) -> Optional[Content]:
        settings = self.parser.settings
        content: Optional[Content] = None
        strip = convert_smart_yes_no(settings.strip_stdin)
        newline: str = settings.newline if settings.newline is not None else os.linesep
        tab: str = settings.tab if settings.tab is not None else '\t'

        if strip is None:
            content = snippet.get_content(False, True, True, tab, newline)
            if content:
                content.text += newline
        elif strip:
            content = snippet.get_content(False, True, True, tab, newline)
        else:
            content = snippet.get_content(False, False, True, tab, newline)
        return content

    def run(self, _: str) -> None:
        stdins: List[Content] = []
        for snippet in self:
            stdin = self.get_content(snippet)
            if stdin:
                stdins.append(stdin)
        for language_name in self.language_names or self.parser.settings.computed_languages():
            self.parser.runner.set_stdins(language_name, stdins)


class CodeSection(Section):
    @staticmethod
    def get_header_match(line: str) -> Optional['re.Match[str]']:
        return re.match(Syntax.CODE_HEADER, line)

    @staticmethod
    def get_content(snippet: Snippet, language: Language) -> Optional[Content]:
        content: Optional[Content] = None
        strip = convert_smart_yes_no(language.strip_code)
        newline: str = language.newline if language.newline is not None else os.linesep
        tab: str = language.tab if language.tab is not None else '\t'

        if strip is None:
            content = snippet.get_content(True, True, True, tab, newline)
            if content:
                content.text += newline
        elif strip:
            content = snippet.get_content(False, True, True, tab, newline)
        else:
            content = snippet.get_content(False, False, True, tab, newline)
        return content

    def run(self, directory: str) -> None:
        for snippet in self:
            for raw_language_name in self.raw_language_names:
                language_name = Language.normalize(raw_language_name)
                if language_name not in self.parser.settings:
                    print_err(f'Language "{raw_language_name.strip()}" on line {self.first_line + 1} '
                              'not found in settings JSON. Skipping language.')
                    continue
                code = self.get_content(snippet, self.parser.settings[language_name])
                if code:
                    self.parser.runner.run(language_name, code, directory)


class Parser:
    def __init__(self, manyfile: str, settings: Settings, runner: Runner) -> None:
        self.settings = settings
        self.runner = runner
        self.lines = manyfile.splitlines()
        self.first_line = self.get_first_line()
        self.last_line = self.get_last_line()
        self.clean_lines()
        self.make_sections()

    def get_first_line(self) -> int:
        for i in range(len(self.lines) - 1, -1, -1):
            if Syntax.string_starts_line(Syntax.START, self.lines[i]):
                return i + 1
        return 0

    def get_last_line(self) -> int:
        for i, line in enumerate(self.lines):
            if Syntax.string_starts_line(Syntax.STOP, line):
                return i - 1
        return len(self.lines) - 1

    def clean_lines(self) -> None:
        for i, line in enumerate(self.lines):
            if i < self.first_line or i > self.last_line or line.startswith(Syntax.LEADING_COMMENT):
                self.lines[i] = ''

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
                elif Syntax.remove_inline_comment(line).strip():
                    print_err(f'Line {i+1} "{line}" is not part of a section. Skipping line.')
            elif Syntax.string_starts_line(Syntax.END, line) or Section.try_get_section_type(line):
                in_section = False
                self.sections.append(section_type(self, section_first_line, i - 1))
                if not Syntax.string_starts_line(Syntax.END, line):
                    i -= 1
            i += 1
        if in_section:
            self.sections.append(section_type(self, section_first_line, self.last_line))

    def __iter__(self) -> Iterator[Section]:
        enabled_sections = [section for section in self.sections if not section.is_disabled]
        solos_found = {SettingsSection: False, ArgvSection: False, StdinSection: False, CodeSection: False}
        for section in enabled_sections:
            if section.is_solo:
                solos_found[type(section)] = True
            if all(solos_found.values()):
                break
        for section in enabled_sections:
            if not solos_found[type(section)] or section.is_solo:
                yield section

    def __str__(self) -> str:
        return pformat(self.sections)  # pragma: no cover

    def __repr__(self) -> str:
        return str(self)  # pragma: no cover
