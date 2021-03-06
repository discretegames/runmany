"""Tests that only the appropriate RunMany functions are imported in a wildcard import."""

# Separate file is needed to test wildcard imports since the syntax is not allowed in functions.
from runmany import *  # pylint: disable=wildcard-import,unused-wildcard-import # noqa


def test_wildcard_imports() -> None:
    assert 'runmany' in globals()
    assert 'runmanys' in globals()
    assert 'cmdline' in globals()
    assert 'main' not in globals()
    assert 'run' not in globals()
