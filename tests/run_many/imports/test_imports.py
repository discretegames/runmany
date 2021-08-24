import pytest


def test_imports() -> None:
    import run_many
    assert hasattr(run_many, 'runmany')
    assert hasattr(run_many, 'runmany_to_s')
    assert hasattr(run_many, 'runmany_to_f')
    assert hasattr(run_many, 'cmdline')
    assert not hasattr(run_many, 'run_iterator')
    assert not hasattr(run_many, 'Placeholders')
    assert not hasattr(run_many, 'CODE_START')


def test_from_imports() -> None:
    from run_many import runmany, runmany_to_s, runmany_to_f, cmdline
    assert 'runmany' in locals()
    assert 'runmany_to_s' in locals()
    assert 'runmany_to_f' in locals()
    assert 'cmdline' in locals()

    with pytest.raises(ImportError):
        from run_many import run_iterator  # type: ignore

    with pytest.raises(ImportError):
        from run_many import Placeholders  # type: ignore

    with pytest.raises(ImportError):
        from run_many import CODE_START  # type: ignore
