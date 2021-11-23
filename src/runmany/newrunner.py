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
    def __init__(self, language: Language, code: Content, filename: str):
        self.language = language
        self.code = code
        self.filename = filename

    def get_command(self, argv: Optional[Content]) -> str:
        return PathParts(self.filename).fill_command(self.language.command, argv.text if argv else '', self.code.text)

    def get_stderr(self) -> int:
        stderr = convert_smart_yes_no(self.language.stderr)
        if stderr is None:
            return subprocess.PIPE
        if stderr:
            return subprocess.STDOUT
        return subprocess.DEVNULL

    def run(self, run_number: int, argv: Optional[Content], stdin: Optional[Content]) -> Tuple[str, str, bool]:
        command = self.get_command(argv)
        stderr = self.get_stderr()
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
            stdout = f'TIMED OUT OF {self.language.timeout:g}s LIMIT'
            exit_code: Union[int, str] = 'T'
        else:
            stdout = result.stdout
            exit_code = result.returncode
            if exit_code != 0 and stderr == subprocess.PIPE:
                stdout += result.stderr

        print(run_number, time_taken)
        # output = self.make_output(run_number, time_taken, exit_code, command, stdout) # TODO
        return 'out', stdout, exit_code == 0


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
            runnable = Runnable(language, code, file.name)

        for argv in self.argvs[language_name] or [cast(Content, None)]:  # Weird cast here since mypy was being a jerk.
            for stdin in self.stdins[language_name] or [cast(Content, None)]:
                self.total_runs += 1
                output, stdout, success = runnable.run(self.total_runs, argv, stdin)
                self.successful_runs += success
                if self.settings.show_runs:
                    print(output, flush=True)
                if self.settings.show_equal:
                    self.equal_stdouts[stdout].append(self.total_runs)
        # TODO make footer based on self.equal_stdouts, etc
        # TODO time whole thing

    def __str__(self) -> str:
        return pformat((self.total_runs, self.successful_runs, self.argvs, self.stdins))

    def __repr__(self) -> str:
        return str(self)
