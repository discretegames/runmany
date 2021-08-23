"""File to quickly run and open html coverage.py report."""

# py runcoverage.py

from subprocess import run

print('Running Coverage...')
run('venv/Scripts/python -m coverage run -m pytest')
run('venv/Scripts/python -m coverage report')
run('venv/Scripts/python -m coverage html')
run('cmd /c start htmlcov/index.html')
print('COVERAGE DONE')
