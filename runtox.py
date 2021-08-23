"""File to quickly run Tox tests."""

# py runtox.py

from subprocess import run

print('Running Tox Tests...')
result = run('venv/Scripts/python -m tox')
# result = run('venv/Scripts/python -m tox -q')
# result = run('venv/Scripts/python -m tox -e py39')
print('TOX RUN DONE', result)
