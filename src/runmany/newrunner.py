"""RunMany runner module. Handles running the code snippets and generating the output."""

from typing import List, Dict
from pprint import pformat
from runmany.settings import Settings


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


class Runner:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.total_runs = 0
        self.successful_runs = 0
        self.argvs: Dict[str, List[str]] = {}
        self.stdins: Dict[str, List[str]] = {}

    def set_argvs(self, language_name: str, argvs: List[str]) -> None:  # TODO take line number too
        self.argvs[language_name] = argvs

    def set_stdins(self, language_name: str, stdins: List[str]) -> None:  # TODO take line number too
        self.stdins[language_name] = stdins

    def run(self, language_name: str, code: str) -> None:
        print(repr((self, language_name, code)))  # TODO

    def __str__(self) -> str:
        return pformat((self.total_runs, self.successful_runs, self.argvs, self.stdins))

    def __repr__(self) -> str:
        return str(self)
