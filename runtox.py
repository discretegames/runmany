"""File to quickly run Tox tests."""

# py runtox.py
# pylint: disable=subprocess-run-check

from subprocess import run

print('Running Tox...')
result = run('venv/Scripts/python -m tox')
# result = run('venv/Scripts/python -m tox -q')
# result = run('venv/Scripts/python -m tox -q -e py39')
run('venv/Scripts/python runcoverage.py')
print('TOX DONE', result)
