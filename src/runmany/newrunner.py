"""RunMany runner module. Handles running the code snippets and generating the output."""

from collections import defaultdict
from typing import DefaultDict, List


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
    def __init__(self) -> None:
        self.total_runs = 0
        self.successful_runs = 0
        self.argvs: DefaultDict[str, List[str]] = defaultdict(list)
        self.stdins: DefaultDict[str, List[str]] = defaultdict(list)
