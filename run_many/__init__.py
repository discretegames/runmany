"""Tool to run .many files, where many programs written in many languages may exist in one file."""

from .runmany import runmany
from .runmany import runmany_to_s
from .runmany import runmany_to_f
from .runmany import cmdline

__all__ = ['runmany', 'runmany_to_s', 'runmany_to_f', 'cmdline']
