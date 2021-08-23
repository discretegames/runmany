"""File to quickly run Tox tests. Call from command line "py runtox.py"."""

from subprocess import run

print('Running Tox Tests...')
print('DONE', run('venv/Scripts/python -m tox -q'))
