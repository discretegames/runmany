"""RunMany runner module. Handles running the code snippets and generating the output."""

from typing import List, Dict
from pprint import pformat
from runmany.settings import Settings
from runmany.util import Content


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
        self.argvs: Dict[str, List[Content]] = {}
        self.stdins: Dict[str, List[Content]] = {}

    def set_argvs(self, language_name: str, argvs: List[Content]) -> None:
        self.argvs[language_name] = argvs

    def set_stdins(self, language_name: str, stdins: List[Content]) -> None:
        self.stdins[language_name] = stdins

    def run(self, language_name: str, code: Content) -> None:
        print(self, language_name, repr(code))

    def __str__(self) -> str:
        return pformat((self.total_runs, self.successful_runs, self.argvs, self.stdins))

    def __repr__(self) -> str:
        return str(self)
