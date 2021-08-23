"""run_many test package."""


# import run_many

# Ways to run on Windows dev machine:
# F5 in vsc with "Debug Tox Tests" configuration
# py runtox.py
# py -m pytest
# py -m coverage run -m pytest THEN py -m coverage report OR py -m coverage html


def inc(x: int) -> int:
    return x + 1


def test_answer() -> None:
    assert inc(1) == 2
    assert inc(4) == 5
