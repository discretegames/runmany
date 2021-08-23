"""File to run Tox tests with VSCode debugger (a rather slow process)."""

# F5 in VSCode with "Debug Tox Tests" configuration

import tox
print('Debugging Tox Tests...')
try:
    tox.cmdline(['-q'])
except SystemExit:
    pass
print('TOX DEBUG DONE')
