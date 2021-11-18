import pytest

# pylint: disable=import-outside-toplevel,possibly-unused-variable,no-name-in-module,unused-import


def test_imports() -> None:
    import runmany
    assert hasattr(runmany, 'runmany')
    assert hasattr(runmany, 'runmany_to_s')
    assert hasattr(runmany, 'runmany_to_f')
    assert hasattr(runmany, 'cmdline')
    assert not hasattr(runmany, 'main')
    assert not hasattr(runmany, 'run_iterator')


def test_from_imports() -> None:
    from runmany import runmany, runmany_to_s, runmany_to_f, cmdline  # noqa
    assert 'runmany' in locals()
    assert 'runmany_to_s' in locals()
    assert 'runmany_to_f' in locals()
    assert 'cmdline' in locals()

    # pylint: disable=no-member
    with pytest.raises(ImportError):
        from runmany import main  # type: ignore # noqa

    with pytest.raises(ImportError):
        from runmany import run_iterator  # type: ignore # noqa
