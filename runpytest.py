"""File to quickly run Pytest tests."""

# py runpytest.py
# pylint: disable=subprocess-run-check

from subprocess import run

print('Running Pytest...')
# result = run('venv/Scripts/python -m pytest')
# result = run('venv/Scripts/python -m pytest -vv')
# result = run('venv/Scripts/python -m pytest -m "not slow"')
result = run('venv/Scripts/python -m pytest -m "not slow" -q')
# result = run('venv/Scripts/python -m pytest -m slow')
# result = run('venv/Scripts/python -m pytest -m "not slow" -vv')
# result = run('venv/Scripts/python -m pytest -m "not slow" -x -vv')
# result = run('venv/Scripts/python -m pytest -q')
print('PYTEST DONE', result)
