"""Test module for run_many package."""
import pathlib
from run_many import runmany_to_s


# Ways to run on Windows dev machine:
# F5 in vsc with "Debug Tox Tests" configuration
# py runtox.py
# pu runcoverage.py
# py -m pytest


def get_file(name: str) -> pathlib.Path:
    return pathlib.Path(__file__).with_name(name)


inp = open(get_file('inp.many')).read()
outp = open(get_file('out.txt')).read()


# one messy test for now
def test_run() -> None:
    assert runmany_to_s(inp, from_string=True).strip() == outp.strip()
