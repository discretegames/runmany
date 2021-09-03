"""Tool to run .many files, where many programs written in many languages may exist in one file."""

from run_many.runmany import runmany
from run_many.runmany import runmany_to_s
from run_many.runmany import runmany_to_f
from run_many.runmany import cmdline

__all__ = ['runmany', 'runmany_to_s', 'runmany_to_f', 'cmdline']
