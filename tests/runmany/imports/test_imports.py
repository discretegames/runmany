import pytest


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

    with pytest.raises(ImportError):
        from runmany import main  # type: ignore # noqa # pylint: disable=no-name-in-module

    with pytest.raises(ImportError):
        from runmany import run_iterator  # type: ignore # noqa # pylint: disable=no-name-in-module
