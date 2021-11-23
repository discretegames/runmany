"""RunMany runner module. Handles running the code snippets and generating the output."""

import os
import time
import subprocess
from pathlib import PurePath
from pprint import pformat
from collections import defaultdict
from typing import List, DefaultDict, Dict, Optional, Union, Tuple, cast
from tempfile import NamedTemporaryFile
from runmany.settings import Settings, Language
from runmany.util import Content, convert_smart_yes_no

DIVIDER_CHAR, SUBDIVIDER_CHAR, DIVIDER_WIDTH = '*', '-', 60


class Placeholders:  # pylint: disable=too-few-public-methods
    prefix = '$'
    ARGV = 'argv'
    CODE = 'code'
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


class PathParts:
    def __init__(self, path: str) -> None:
        def quote(string: str) -> str:
            return f'"{string}"'
        purepath = PurePath(path)
        self.parts: Dict[str, str] = {}
        self.parts[Placeholders.RAWDIR] = str(purepath.parent)
        self.parts[Placeholders.DIR] = quote(self.parts[Placeholders.RAWDIR])
        self.parts[Placeholders.RAWFILE] = str(purepath)
        self.parts[Placeholders.FILE] = quote(self.parts[Placeholders.RAWFILE])
        self.parts[Placeholders.RAWBRANCH] = str(purepath.with_suffix(''))
        self.parts[Placeholders.BRANCH] = quote(self.parts[Placeholders.RAWBRANCH])
        self.parts[Placeholders.NAME] = purepath.name
        self.parts[Placeholders.STEM] = purepath.stem
        self.parts[Placeholders.EXT] = purepath.suffix
        self.parts[Placeholders.SEP] = os.sep

    @staticmethod
    def fill_part(command: str, part: str, fill: str) -> str:
        return command.replace(f'{Placeholders.prefix}{part}', fill)

    def fill_command(self, command: str, argv: str, code: str) -> str:
        if Placeholders.prefix not in command:
            command += f' {self.parts[Placeholders.FILE]}'
            if argv:
                command += f' {argv}'
        else:
            for part, fill in self.parts.items():
                command = self.fill_part(command, part, fill)
            command = self.fill_part(command, Placeholders.ARGV, argv)
            command = self.fill_part(command, Placeholders.CODE, code)
        return command


class Runnable:
    def __init__(self, settings: Settings, language: Language, code: Content, filename: str):
        self.settings = settings
        self.language = language
        self.code = code
        self.filename = filename

    def get_command(self, argv: Optional[Content]) -> str:
        return PathParts(self.filename).fill_command(self.language.command, argv.text if argv else '', self.code.text)

    def get_stderr(self) -> int:
        show_stderr = convert_smart_yes_no(self.language.show_stderr)
        if show_stderr is None:
            return subprocess.PIPE
        if show_stderr:
            return subprocess.STDOUT
        return subprocess.DEVNULL

    def run(self, run_number: int, argv: Optional[Content], stdin: Optional[Content]) -> Tuple[str, bool]:
        command = self.get_command(argv)
        stderr = self.get_stderr()
        if self.language.show_runs:
            self.start_printing_headline(run_number)

        start_time = time.perf_counter()
        try:
            result = subprocess.run(command,
                                    input=stdin.text if stdin else '',
                                    timeout=self.language.timeout,
                                    shell=True,
                                    check=False,
                                    universal_newlines=True,  # Backwards compatible with 3.6.
                                    stdout=subprocess.PIPE,
                                    stderr=stderr)
            time_taken = time.perf_counter() - start_time
        except subprocess.TimeoutExpired:
            time_taken = time.perf_counter() - start_time
            output = f'TIMED OUT OF {self.language.timeout:g}s LIMIT'
            exit_code: Union[int, str] = 'T'
        else:
            output = result.stdout
            exit_code = result.returncode
            if exit_code != 0 and stderr == subprocess.PIPE:
                output += result.stderr

        if self.language.show_runs:
            self.finish_printing_headline(time_taken, exit_code, command)
            self.print_results(argv, stdin, output)
        return output, exit_code == 0

    def start_printing_headline(self, run_number: int) -> None:
        if not self.settings.minimalist:
            print(DIVIDER_CHAR * DIVIDER_WIDTH)
        print(f'{run_number}. {self.language.name}', flush=True, end='')

    def finish_printing_headline(self, time_taken: float, exit_code: Union[str, int], command: str) -> None:
        headline = []
        if self.language.show_time:
            headline.append(f' ({time_taken:.3f}s)')
        if exit_code != 0:
            headline.append(f' [exit code {exit_code}]')
        if self.language.show_command:
            headline.append(f' > {command}')
        print(''.join(headline))

    def print_results(self, argv: Optional[Content], stdin: Optional[Content], output: str) -> None:
        # parts: List[str] = []
        pass
        # if not self.minimalist:

        # TODO strip output

        # TODO do "1. Python" part first on flush print
        # 1. Python (3.1s) [exit code 1] > "python myfile.py"

    #     if self.language_data.show_code:
    #         parts.append(self.make_output_part('code at', self.code_section))
    #     if self.argv_section and self.argv_section.content and self.language_data.show_argv:
    #         parts.append(self.make_output_part('argv at', self.argv_section))
    #     if self.stdin_section and self.stdin_section.content and self.language_data.show_stdin:
    #         parts.append(self.make_output_part('stdin at', self.stdin_section))
    #     if self.language_data.show_output:
    #         parts.append(self.make_output_part('output from', self.code_section, stdout))

    #     return '\n'.join(parts) + '\n' * cast(int, self.language_data.spacing)


class Runner:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.total_runs = 0
        self.successful_runs = 0
        self.argvs: DefaultDict[str, List[Content]] = defaultdict(list)
        self.stdins: DefaultDict[str, List[Content]] = defaultdict(list)
        self.equal_stdouts: DefaultDict[str, List[int]] = defaultdict(list)

    def set_argvs(self, language_name: str, argvs: List[Content]) -> None:
        self.argvs[language_name] = argvs

    def set_stdins(self, language_name: str, stdins: List[Content]) -> None:
        self.stdins[language_name] = stdins

    def run(self, language_name: str, code: Content, directory: str) -> None:
        language = self.settings[language_name]
        with NamedTemporaryFile(mode='w', suffix=language.extension, dir=directory, delete=False) as file:
            file.write(code.text)
            runnable = Runnable(self.settings, language, code, file.name)

        for argv in self.argvs[language_name] or [cast(Content, None)]:  # Weird cast here since mypy was being a jerk.
            for stdin in self.stdins[language_name] or [cast(Content, None)]:
                self.total_runs += 1
                stdout, success = runnable.run(self.total_runs, argv, stdin)
                self.successful_runs += success
                if self.settings.show_equal:
                    self.equal_stdouts[stdout].append(self.total_runs)
        # TODO make footer based on self.equal_stdouts, etc
        # TODO time whole thing

    def __str__(self) -> str:
        return pformat((self.total_runs, self.successful_runs, self.argvs, self.stdins))

    def __repr__(self) -> str:
        return str(self)
