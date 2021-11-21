"""delete/redo"""
# import os
# import io
# import time
# import pathlib
# import subprocess
# from collections import defaultdict

# from runmany.util import print_err
# # from runmany.settings import load_settings, Settings, LanguageData, normalize
# from runmany.newsettings import NewSettings
# from runmany.parser import section_iterator, Section, SectionType, Syntax

# OUTPUT_FILL_CHAR, OUTPUT_FILL_WIDTH = '-', 60
# OUTPUT_DIVIDER = OUTPUT_FILL_WIDTH * '*'
# STDERR_NZEC, STDERR_NEVER = ('nzec', None), ('never', False)


# from typing import List, DefaultDict, Optional, Union, Tuple, Iterator, Generator, TextIO, cast
# from tempfile import TemporaryDirectory
from runmany.settings import Settings
from runmany.newparser import Parser


class Placeholders:  # pylint: disable=too-few-public-methods
    prefix = '$'
    ARGV = 'argv'
    # For file .../dir/file.ext the parts are:
    RAWDIR = 'rawdir'        # .../dir
    DIR = 'dir'              # ".../dir"
    RAWFILE = 'rawfile'      # .../dir/file.ext
    FILE = 'file'            # ".../dir/file.ext"
    RAWBRANCH = 'rawbranch'  # .../dir/file
    BRANCH = 'branch'        # ".../dir/file"
    NAME = 'name'            # file.ext
    STEM = 'stem'            # file
    EXT = 'ext'              # .ext
    SEP = 'sep'              # /


def run(manyfile: str, settings: Settings) -> None:
    parser = Parser(manyfile, settings)
    for section in parser:
        section.run()

    # with TemporaryDirectory() as directory:
    # for section in parser.get_sections():
    #     pass
    # for also in section.get_alsos():
    #     print(also)

# total_runs, successful_runs = 0, 0
# equal_stdouts: DefaultDict[str, List[int]] = defaultdict(list)
# with io.StringIO(manyfile) as file, TemporaryDirectory() as directory:
#     iterator = run_iterator(file)
#     settings = load_settings(settings, cast(str, next(iterator)))
#     iterator.send(settings)

#     for a_run in cast(Iterator[Run], iterator):
#         run_number = total_runs + 1
#         output, stdout, success = a_run.run(directory, run_number)
#         total_runs += 1
#         successful_runs += success
#         if settings.show_runs:
#             print(output, flush=True)
#         if settings.show_equal:
#             equal_stdouts[stdout].append(run_number)
#     print(make_footer(settings, total_runs, successful_runs, equal_stdouts), flush=True)

# class PathParts:
#     def __init__(self, path: str) -> None:
#         def quote(string: str) -> str:
#             return f'"{string}"'
#         purepath = pathlib.PurePath(path)
#         self.parts: Dict[str, str] = {}
#         self.parts[Placeholders.RAWDIR] = str(purepath.parent)
#         self.parts[Placeholders.DIR] = quote(self.parts[Placeholders.RAWDIR])
#         self.parts[Placeholders.RAWFILE] = str(purepath)
#         self.parts[Placeholders.FILE] = quote(self.parts[Placeholders.RAWFILE])
#         self.parts[Placeholders.RAWBRANCH] = str(purepath.with_suffix(''))
#         self.parts[Placeholders.BRANCH] = quote(self.parts[Placeholders.RAWBRANCH])
#         self.parts[Placeholders.NAME] = purepath.name
#         self.parts[Placeholders.STEM] = purepath.stem
#         self.parts[Placeholders.EXT] = purepath.suffix
#         self.parts[Placeholders.SEP] = os.sep

#     @staticmethod
#     def fill_part(command: str, part: str, fill: str) -> str:
#         return command.replace(f'{Placeholders.prefix}{part}', fill)

#     def fill_command(self, command: str, argv: str) -> str:
#         if Placeholders.prefix not in command:
#             command += f' {self.parts[Placeholders.FILE]}'
#             if argv:
#                 command += f' {argv}'
#         else:
#             for part, fill in self.parts.items():
#                 command = self.fill_part(command, part, fill)
#             command = self.fill_part(command, Placeholders.ARGV, argv)
#         return command

# class Run:
#     def __init__(self, code_section: Section, argv_section: Optional[Section], stdin_section: Optional[Section],
#                  language_data: LanguageData) -> None:
#         self.code_section = code_section
#         self.argv_section = argv_section
#         self.stdin_section = stdin_section
#         self.language_data = language_data

#     def get_stderr(self) -> int:
#         if self.language_data.stderr in STDERR_NZEC:
#             return subprocess.PIPE
#         if self.language_data.stderr in STDERR_NEVER:
#             return subprocess.DEVNULL
#         return subprocess.STDOUT

#     def run(self, directory: str, run_number: int) -> Tuple[str, str, bool]:
#         with NamedTemporaryFile(mode='w', suffix=self.language_data.ext, dir=directory, delete=False) as code_file:
#             code_file.write(self.code_section.content)
#             code_file_name = code_file.name

#         argv = self.argv_section.content if self.argv_section else ''
#         stdin = self.stdin_section.content if self.stdin_section and self.stdin_section.content else None
#         command = PathParts(code_file_name).fill_command(cast(str, self.language_data.command), argv)

#         start_time = time.perf_counter()
#         try:
#             # Using universal_newlines=True instead of text=True here for backwards compatability with Python 3.6.
#             result = subprocess.run(command, input=stdin, timeout=self.language_data.timeout, shell=True, check=False,
#                                     universal_newlines=True, stdout=subprocess.PIPE, stderr=self.get_stderr())
#             time_taken = time.perf_counter() - start_time
#         except subprocess.TimeoutExpired:
#             time_taken = time.perf_counter() - start_time
#             stdout = f'TIMED OUT OF {self.language_data.timeout:g}s LIMIT'
#             exit_code: Union[int, str] = 'T'
#         else:
#             stdout = result.stdout
#             exit_code = result.returncode
#             if exit_code != 0 and self.language_data.stderr in STDERR_NZEC:
#                 stdout += result.stderr

#         output = self.make_output(run_number, time_taken, exit_code, command, stdout)
#         return output, stdout, exit_code == 0

#     @staticmethod
#     def make_output_part(title: str, section: Section, content: Optional[str] = None) -> str:
#         if content is None:
#             content = section.content.strip('\r\n')
#         return f'{f" {title} line {section.line_number} ":{OUTPUT_FILL_CHAR}^{OUTPUT_FILL_WIDTH}}\n{content}'

#     def make_output(self, run_number: int, time_taken: float,  # pylint: disable=too-many-arguments
#                     exit_code: Union[int, str], command: str, stdout: str) -> str:
#         parts = [OUTPUT_DIVIDER]

#         headline = f'{run_number}. {self.language_data.name}'
#         if self.language_data.show_time:
#             headline += f' ({time_taken:.2f}s)'
#         if exit_code != 0:
#             headline += f' [exit code {exit_code}]'
#         if self.language_data.show_command:
#             headline += f' > {command}'
#         parts.append(headline)

#         if self.language_data.show_code:
#             parts.append(self.make_output_part('code at', self.code_section))
#         if self.argv_section and self.argv_section.content and self.language_data.show_argv:
#             parts.append(self.make_output_part('argv at', self.argv_section))
#         if self.stdin_section and self.stdin_section.content and self.language_data.show_stdin:
#             parts.append(self.make_output_part('stdin at', self.stdin_section))
#         if self.language_data.show_output:
#             parts.append(self.make_output_part('output from', self.code_section, stdout))

#         return '\n'.join(parts) + '\n' * cast(int, self.language_data.spacing)

# def make_footer(settings: Settings, total_runs: int, successful_runs: int,
#                 equal_stdouts: DefaultDict[str, List[int]]) -> str:
#     parts = [OUTPUT_DIVIDER]

#     if settings.show_stats:
#         line = f'{successful_runs}/{total_runs} program{"" if total_runs == 1 else "s"} successfully run'
#         if successful_runs < total_runs:
#             line += f'. {total_runs - successful_runs} failed due to non-zero exit code or timeout.'
#         else:
#             line += '!'
#         parts.append(line)

#     if settings.show_equal:
#         groups = sorted(equal_stdouts.values(), key=len)
#         biggest = len(groups[-1]) if groups else 0
#         line = f'{biggest}/{total_runs} had the exact same stdout'
#         if biggest != total_runs:
#             line += '. Equal runs grouped: ' + ' '.join('[' + ' '.join(map(str, group)) + ']' for group in groups)
#         else:
#             line += '!'
#         parts.append(line)

#     if len(parts) > 1:
#         parts.append(OUTPUT_DIVIDER)

#     return '\n'.join(parts)

# def run_iterator(file: TextIO) -> Generator[Union[str, None, Run], Settings, None]:
#     lead_section: Optional[Section] = None
#     argvs: DefaultDict[str, List[Optional[Section]]] = defaultdict(lambda: [None])
#     stdins: DefaultDict[str, List[Optional[Section]]] = defaultdict(lambda: [None])

#     iterator = section_iterator(file)
#     settings = yield cast(str, next(iterator))  # pylint: disable=stop-iteration-return
#     yield None  # Extra yield needed to send back to the send from runmany_to_f. Not ready to yield runs yet.
#     iterator.send(settings)

#     for section in cast(Iterator[Section], iterator):
#         if not section.is_also:
#             lead_section = section
#         if not lead_section and not section.is_disabled:
#             print_err(f'No lead section for {Syntax.ALSO} on line {section.line_number}. Skipping section.')
#             continue
#         lead_section = cast(Section, lead_section)
#         if section.is_disabled or lead_section.is_disabled:
#             continue

#         if section.type in (SectionType.ARGV, SectionType.STDIN):
#             input_dict = argvs if section.type is SectionType.ARGV else stdins
#             for language in lead_section.languages:
#                 language = normalize(language)
#                 if not section.is_also:
#                     input_dict[language].clear()
#                 input_dict[language].append(section)
#         else:
#             for language in lead_section.languages:
#                 if language not in settings:
#                     line_number = lead_section.line_number
#                     print_err(
#                         f'Language "{language}" on line {line_number} not found in settings JSON. Skipping language.')
#                     continue
#                 language = normalize(language)
#                 for argv_section in argvs[language]:
#                     for stdin_section in stdins[language]:
#                         yield Run(section, argv_section, stdin_section, settings[language])
