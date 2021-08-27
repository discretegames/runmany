
# [RunMany](https://pypi.org/project/run-many/)

**A tool to run many programs written in many languages from one file.**

Suppose you want to practice multiple programming languages at once. Normally you'd have to juggle multiple files or multiple projects, perhaps multiple IDEs. RunMany lets you write multiple programs in *the same* file using any programming languages you like, and then run them all at once.

In general RunMany can be used for:

- Crestomathy - Writing programs that do the same thing in many languages, like
 [Rosetta Code](http://www.rosettacode.org/wiki/Rosetta_Code).
 ([example](https://github.com/discretegames/runmany/blob/main/examples/helloworld.many)/[output](https://github.com/discretegames/runmany/blob/main/examples/helloworld_output.txt))
- Performance Testing - Timing different implementations of a program, even across languages.
 ([example](https://github.com/discretegames/runmany/blob/main/examples/primes.many)/[output](https://github.com/discretegames/runmany/blob/main/examples/primes_output.txt))
- Input Testing - Easily giving many combinations of argv or stdin input to programs.
 ([example](https://github.com/discretegames/runmany/blob/main/examples/inputs.many)/[output](https://github.com/discretegames/runmany/blob/main/examples/inputs_output.txt))
- Creating Polyglots - Esoteric programs that can be executed in multiple languages.
 ([example](https://github.com/discretegames/runmany/blob/main/examples/polyglot.many)/[output](https://github.com/discretegames/runmany/blob/main/examples/polyglot_output.txt))

# Installation (supports Python 3.6+)

```console
pip install run-many
```

[PyPI Package Page](https://pypi.org/project/run-many/) | [TestPyPI bleeding edge version](https://test.pypi.org/project/run-many/)

# Usage

## Command Line

```console
> runmany [-h] [-j <json-file>] [-o <output-file>] <input-file>

Runs a .many file.

positional arguments:
  <input-file>          the .many file to run

optional arguments:
  -h, --help            show this help message and exit
  -j <settings-file>, --json <settings-file>
                        the .json settings file to use
  -o <output-file>, --output <output-file>
                        the file output is redirected to
```

By default output goes to stdout and [default_settings.json](https://github.com/discretegames/runmany/blob/main/run_many/default_settings.json) is used as a fallback when a custom settings json is not provided or is missing any settings.

See [the examples folder](https://github.com/discretegames/runmany/tree/main/examples) for some .many files to try. Note that they were run on a Windows machine with the necessary interpreters and compilers installed.

## From Python

```py
from run_many import runmany, runmany_to_s, runmany_to_f

# Run to stdout
runmany('path/to/input.many', 'path/to/settings.json') # settings json is always optional

# Run to output file
runmany('path/to/input.many', 'path/to/settings.json', 'path/to/output.txt')

# Run to string
result = runmany_to_s('path/to/input.many', 'path/to/settings.json')

# Run to file object
with open('output.txt', 'w') as f:
    runmany_to_f(f, 'path/to/input.many', 'path/to/settings.json')
```

As with the command line, [default_settings.json](https://github.com/discretegames/runmany/blob/main/run_many/default_settings.json) is used as a fallback for all settings.

In each of the 3 runmany functions, the setting json argument may be given as a path to the .json file or a corresponding Python dictionary.  
Additionally, the many file contents may be given as a string rather than a path with `from_string=True`.

`run_many.cmdline` is also present as an alternative to using the command line directly.

# .many Syntax

TODO - describe with examples

- \~\~\~| code
  - \~\~\~|~~~ lists
- \$\$\$| stdin
  - \$\$\$|\$\$\$ lists
- @@@| argv
  - @@@|@@@ lists
- %%%| comments
- %%%|%%% exit

# Settings

TODO - describe possible values and behavior of every setting, how to read the output

# About

TODO?
