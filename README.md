
# RunMany

**A tool to run many programs written in many languages from one file.**

Suppose you want to practice multiple programming languages at once. Normally you'd have to juggle multiple files or multiple projects, perhaps multiple IDEs. RunMany lets you write multiple programs in *the same* file using any programming languages you like, and then run them all at once with shared inputs.

In general RunMany can be used for:

- Crestomathy - Writing programs that do the same thing in many languages, like what [Rosetta Code](http://www.rosettacode.org/wiki/Rosetta_Code) does. ([example](https://github.com/discretegames/runmany/blob/main/examples/helloworld.many)/[output](https://github.com/discretegames/runmany/blob/main/examples/helloworld_output.txt))
- Performance Testing - Easily testing and timing many slight variants of a program. (todo example)
- Input Testing - Easily giving many combinations of argv or stdin input to a program. (todo example)
- Creating Polyglots - Esoteric programs that can be executed in multiple languages. ([example](https://github.com/discretegames/runmany/blob/main/examples/polyglot.many)/[output](https://github.com/discretegames/runmany/blob/main/examples/polyglot_output.txt))

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

See [the examples folder](https://github.com/discretegames/runmany/tree/main/examples) for some files to try.
Todo - mention that languages must be installed.

## From Python

```py
from run_many import runmany, runmany_to_s, runmany_to_f

todo - describe each function
```

todo mention cmdline
