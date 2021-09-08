# Separate file is needed to test wildcard imports since the syntax is not allowed in functions.
from runmany import *


def test_wildcard_imports() -> None:
    assert 'runmany' in globals()
    assert 'runmany_to_s' in globals()
    assert 'runmany_to_f' in globals()
    assert 'cmdline' in globals()
    assert 'main' not in globals()
    assert 'run_iterator' not in globals()