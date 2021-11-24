"""Tests that only the appropriate RunMany functions can be imported."""

# pylint: disable=import-outside-toplevel,possibly-unused-variable,no-name-in-module,unused-import
import pytest


def test_imports() -> None:
    import runmany
    assert hasattr(runmany, 'runmany')
    assert hasattr(runmany, 'runmany')
    assert hasattr(runmany, 'cmdline')
    assert not hasattr(runmany, 'main')
    assert not hasattr(runmany, 'run')


def test_from_imports() -> None:
    from runmany import runmany, runmanys, cmdline  # noqa
    assert 'runmany' in locals()
    assert 'runmanys' in locals()
    assert 'cmdline' in locals()

    # pylint: disable=no-member
    with pytest.raises(ImportError):
        from runmany import main  # type: ignore # noqa

    with pytest.raises(ImportError):
        from runmany import run  # type: ignore # noqa
