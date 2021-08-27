<!-- markdownlint-disable-next-line MD041 -->
[![PyPI Version](https://badge.fury.io/py/run-many.svg)](https://badge.fury.io/py/run-many)
 [![Test Coverage](https://raw.githubusercontent.com/discretegames/runmany/main/coverage.svg)](https://github.com/discretegames/runmany/blob/main/coverage.txt)
 [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/run-many)](https://www.python.org/downloads/)

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

todo show basic input and output

# Installation (supports Python 3.6+)

```text
pip install run-many
```

[PyPI Package Page](https://pypi.org/project/run-many/) | [TestPyPI bleeding edge version](https://test.pypi.org/project/run-many/)

# Usage

## Command Line

```text
runmany myfile.many
```

More generally

```text
runmany [-h --help] [-j --json <settings-file>] [-o --output <output-file>] <input-file>
```

- `<input-file>` is the required .many file to run
- `<settings-json>` is the optional .json file that defines how languages are run and how the output is formatted
- `<output-file>` is the optional file to send the output to

By default, output goes to stdout and [default_settings.json](https://github.com/discretegames/runmany/blob/main/run_many/default_settings.json) is used as a fallback when a custom settings json is not provided or is missing any settings.

See [the examples folder](https://github.com/discretegames/runmany/tree/main/examples) for some .many files to try. Note that they were run on a Windows machine with the necessary interpreters and compilers installed.

The [default JSON](https://github.com/discretegames/runmany/blob/main/run_many/default_settings.json#L18) has preset commands for a handful of languages, namely Python, Python 2, JavaScript, TypeScript, Java, Kotlin, Rust, Go, C, C++, and C#. But any of these can be overridden and new languages can be added by populating the "languages" key in a custom JSON. (todo link to more details below)

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

In each of the 3 runmany functions, the settings JSON argument may be given as a path to the .json file or a corresponding Python dictionary.

Additionally, the many file contents may be given as a string rather than a file path with `from_string=True`.

The function `run_many.cmdline` is also present as an alternative to using the command line directly.

# .many Syntax

The .many file format is what runmany expects when given a file to run. (Though, of course, ".many" is not required as an extension.) Since .many files may contain syntax from arbitrary programming languages, a small, unique set of syntax was required to demarcate the various parts.

## Comments and EOF Trigger

Though not crucial, comments and a way to prematurely exit are provided for convenience as part of the .many file syntax.

Any line in a .many file starting with `%%%|` and ending `|%%%` (possibly with trailing whitespace) is considered a comment and is completely ignored.

```test
%%%| this is a comment |%%%
```

The line `%%%|%%%` alone (possibly with trailing whitespace) is considered an end-of-file trigger, and everything after it in the entire file is ignored. `!` may be put before it, e.g. `!%%%|%%%`, to disable the trigger.

## Sections & Delimiters

Aside from comments and the EOF trigger, a .many file can be split into a number of sections, each of which occupies its own contiguous block of lines and is headed by a section delimiter.

A section delimiter must reside on its own line with no leading whitespace, but may have trailing whitespace.

Putting `!` at the front of any section delimiter disables it and its entire section until the next delimiter.

The part before the very first delimiter in a .many file is treated as a comment area and gets copied to the prologue part of the output (todo see below). Otherwise, lines that are not section delimiters are treated as part of the content of the section of the last delimiter.

**There are 6 types of section delimiters:**

1. Code Header: `~~~| language1 | language2 | language3 | ... |~~~`  
   - A `|` separated list of languages, (though usually just one suffices) starting `~~~|` and ending `|~~~`.  
   - The section content is treated as code that will be run in each language in the list in turn.  
   - The language names must match language names in the settings JSON which defines how they are run.

2. Code Header Repeat: `~~~|~~~`  
   - Expects to appear after a Code Header section and is merely shorthand for repeating the exact same Code Header delimiter.

3. Argv Header: `@@@| language1 | language2 | language3 | ... |@@@`  
   - A `|` separated list of languages, starting `@@@|` and ending `|@@@` (`@` for ***a***rgv).  
   - The section content is stripped of newlines and will be used as the command line arguments for the listed languages in any subsequent code sections.  
   - Overwrites any previous Argv Header and Argv List sections for the listed languages.

4. Argv List: `@@@|@@@`  
   - Expects to appear after an Argv Header section or another Argv List section.  
   - The section content is stripped of newlines and added to the list of successive argv inputs to give to the languages listed in the header.  
   - In this way, multiple argv inputs may be tested without code duplication.

5. Stdin Header: `$$$| language1 | language2 | language3 | ... |$$$`  
   - A `|` separated list of languages, starting `$$$|` and ending `|$$$` (`$` for ***s***tdin).  
   - The section content is stripped of newlines (except one left trailing) and will be used as the stdin for the listed languages in any subsequent code sections.  
   - Overwrites any previous Stdin Header and Stdin List sections for the listed languages.

6. Stdin List: `$$$|$$$`  
   - Expects to appear after a Stdin Header section or another Stdin List section.  
   - The section content is stripped of newlines (except one left trailing) and added to the list of successive stdin inputs to give to the languages listed in the header.  
   - In this way, multiple stdin inputs may be tested without code duplication.

The language names in the Code Header, Argv Header, and Stdin Header are always stripped of whitespace and made lowercase before checking if they match a language defined in the settings JSON. The special keyword `All` can be used as a language name and it will auto-expand to all the languages defined in the settings JSON. This is useful for giving the same argv or stdin to all programs. (todo mention how it can be changed below)

## Syntax Example

todo

# Settings JSON

TODO - describe possible values and behavior of every setting, how to read the output

command formatting

# About

TODO?
inspiration
more todo - syntax highlighting?

TODO - mention default languages

Basic .many example containing Python and JavaScript programs: todo ?

```text
~~~| Python |~~~
print('Hello, Python!')

~~~| JavaScript |~~~
console.log('Hello, JS!')
```
