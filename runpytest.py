"""File to quickly run Pytest tests."""

# py runpytest.py

from subprocess import run

print('Running Pytest...')
# result = run('venv/Scripts/python -m pytest')
result = run('venv/Scripts/python -m pytest -m "not slow"')
# result = run('venv/Scripts/python -m pytest -m "not slow" -vv')
# result = run('venv/Scripts/python  -m pytest -m "not slow" -q')
print('PYTEST DONE', result)
