"""File to run Tox tests with VSCode debugger (a rather slow process)."""

# F5 in VSCode with "Debug Tox Tests" configuration

import tox

# options = []
# options = ['-q']
options = ['-q', '-e', 'py39']

print('Debugging Tox Tests...')
try:
    tox.cmdline(options)
except SystemExit:
    pass
print('TOX DEBUG DONE')
