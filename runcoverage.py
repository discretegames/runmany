"""File to quickly run and open html coverage.py report."""

# py runcoverage.py

import os
from subprocess import run

print('Running Coverage...')
run('venv/Scripts/python -m coverage run -m pytest')

try:
    os.remove('coverage.svg')
except FileNotFoundError:
    pass
run('venv/Scripts/python -m coverage_badge -o coverage.svg')

try:
    os.remove('coverage.txt')
except FileNotFoundError:
    pass
run('venv\\Scripts\\python -m coverage report > coverage.txt', shell=True)

run('venv/Scripts/python -m coverage report')
run('venv/Scripts/python -m coverage html')
run('cmd /c start htmlcov/index.html')
print('COVERAGE DONE')
