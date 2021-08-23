"""File to run Tox tests with VSCode debugger (a rather slow process)."""

import tox
print('Debugging Tox Tests...')
try:
    tox.cmdline(['-q'])
except SystemExit:
    pass
print('DONE')
