<!-- markdownlint-disable-next-line MD041 -->
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/runmany)](https://www.python.org/downloads/)
[![Test Coverage](https://raw.githubusercontent.com/discretegames/runmany/main/coverage.svg)
](https://github.com/discretegames/runmany/blob/main/coverage.txt)

# [RunMany](https://pypi.org/project/runmany/)

**[Intro](https://github.com/discretegames/runmany#runmany) |
[Installation](https://github.com/discretegames/runmany#installation) |
[Usage](https://github.com/discretegames/runmany#usage) |
[Syntax](https://github.com/discretegames/runmany#many-syntax) |
[Settings](https://github.com/discretegames/runmany#settings) |
[About](https://github.com/discretegames/runmany#about)**

**A tool to run many programs written in many languages from one file.**

Normally to practice multiple programming languages at once you need multiple files or multiple projects,
perhaps multiple IDE's. RunMany is a tool that lets you write multiple programs in _the same_ file using
any programming languages you want, and then run them all at once.

RunMany uses ".many" as its file extension, so for example, if a file called `simple.many` has the following contents:

```text
Python:
    print("Hi")

JavaScript:
    console.log("Hi")

C:
    #include <stdio.h>
    int main() {
        printf("Hi\n");
        return 0;
    }
```

Then doing `runmany simple.many` in terminal will produce this organized output
of running the Python, JavaScript, and C programs within:

```text
************************************************************
1. Python
-------------------- output from line 1 --------------------
Hi


************************************************************
2. JavaScript
-------------------- output from line 4 --------------------
Hi


************************************************************
3. C
-------------------- output from line 7 --------------------
Hi


************************************************************
3/3 programs successfully run!
3/3 had the exact same stdout!
************************************************************
```

Argv and stdin can also be specified in the .many file on a per-language basis, and there are many
[settings](https://github.com/discretegames/runmany#settings)
that can customize how languages are run and displayed in the output.

In general, RunMany can be used for:

- Chrestomathy - Writing equivalent programs in many languages, like on
[Rosetta Code](http://www.rosettacode.org/wiki/Rosetta_Code).
([example](https://github.com/discretegames/runmany/blob/main/examples/helloworld.many)/
[output](https://github.com/discretegames/runmany/blob/main/examples/helloworld_output.txt))
- Performance Testing - Timing different implementations of a program, even across languages.
([example](https://github.com/discretegames/runmany/blob/main/examples/primes.many)/
[output](https://github.com/discretegames/runmany/blob/main/examples/primes_output.txt))
- Input Testing - Easily giving many combinations of argv or stdin to programs.
([example](https://github.com/discretegames/runmany/blob/main/examples/inputs.many)/
[output](https://github.com/discretegames/runmany/blob/main/examples/inputs_output.txt))
- Polyglots - Making esoteric code that can be executed in multiple languages at once.
([example](https://github.com/discretegames/runmany/blob/main/examples/polyglot.many)/
[output](https://github.com/discretegames/runmany/blob/main/examples/polyglot_output.txt))

Overall RunMany is a useful tool for anyone who wants to play with multiple programming languages at a time.

# Installation

Make sure you have [Python](https://www.python.org/downloads/) version 3.6 or above installed, then run

```text
pip install runmany
```

in terminal to install the latest [RunMany Python package from PyPI](https://pypi.org/project/runmany/).
Then `runmany <filename>` should work to run .many files. See more ways to run in
[Usage](https://github.com/discretegames/runmany#usage).

RunMany works best in [VSCode](https://code.visualstudio.com/) with the companion
[RunMany VSCode extension](https://marketplace.visualstudio.com/items?itemName=discretegames.runmany) which provides
syntax highlighting for .many files and quick ways to run them.
Install the extension for free
[from the marketplace](https://marketplace.visualstudio.com/items?itemName=discretegames.runmany)
or by running:

```text
code --install-extension discretegames.runmany
```

You also need the programming languages you want RunMany to run installed on your computer
because RunMany uses their interpreters/compilers behind the scenes to actually run programs.

RunMany has built-in support for the following languages:

> Ada, Bash, Batch, C, C#, C++, Dart, Fortran, Go, Groovy, Haskell, Java, JavaScript,
Julia, Kotlin, Lisp, Lua, MIPS, Pascal, Perl, PHP, PowerShell, Print, Python, Python 2,
R, Racket, Ruby, Rust, Scala, TypeScript, VBScript, and Visual Basic

Meaning, if you already have one of these languages installed,
there's a good chance it will work in RunMany automatically.

There are ways to add custom languages and change the behavior of built-in languages, and even make them different on
different operating systems. For more info see
[Customizing Languages](https://github.com/discretegames/runmany#customizing-languages).

The [RunMany VSCode extension](https://marketplace.visualstudio.com/items?itemName=discretegames.runmany)
provides syntax highlighting for a few more languages than those listed above.

Note that `Print` is a utility language that simply prints the code content to stdout, and
`MIPS` expects `mars.jar` to be in the current working directory. The RunMany VSCode extension
provides syntax

## Troubleshooting

If `pip install runmany` didn't work try
`pip3 install runmany` or `python -m pip install runmany` or `python3 -m pip install runmany`.

On Windows, if nothing works, you may need to [make sure the Python installation and Scripts directories are in your
Path environment variable](https://datatofish.com/add-python-to-windows-path/),
then restart your terminal and try again.

RunMany was made in Python 3.9 on Windows and has been
[thoroughly tested](https://github.com/discretegames/runmany/blob/main/coverage.txt)
on Python versions 3.6, 3.7, 3.8, 3.9, and 3.10 on Windows.
It should also work fine on Linux and macOS but has been less extensively tested on those operating systems,
especially when it comes to
[the commands](https://github.com/discretegames/runmany/blob/main/src/runmany/default_settings.json#L51)
that run the interpreters/compilers of other programming languages.

RunMany is now in version 2 with improved .many file syntax and more settings.
[The old 1.0.3 version is still available on PyPI.](https://pypi.org/project/runmany/1.0.3/)

# Usage

## Running RunMany From Command Line

To run a RunMany file named `myfile.many` use the terminal command:

```text
runmany myfile.many
```

There are also optional arguments to get help and specify the settings and output files:

```text
runmany [-h --help] [-s --settings <settings-file>] [-o --outfile <output-file>] <input-file>
```

- `<input-file>` is the required .many file to run.
- `<settings-file>` is the optional .json file that defines how languages are run and how the output is formatted.
- `<output-file>` is the optional file to send the output to. When omitted, output goes to stdout.

For example, the command to run `myfile.many` with settings `mysettings.json`
and send output to `myoutput.txt` would be:

```text
runmany -s mysettings.json -o myoutput.txt myfile.many
```

When a settings file is provided on command line, any
[settings sections](https://github.com/discretegames/runmany#settings-section) embedded in the input file are ignored.
If neither are present, or for any missing settings,
[default_settings.json](https://github.com/discretegames/runmany/blob/main/src/runmany/default_settings.json)
is used as a fallback. See more info in [Settings](https://github.com/discretegames/runmany#settings).

For some examples of .many files and their output check
[the examples folder on GitHub](https://github.com/discretegames/runmany/tree/main/examples).

The .many extension for RunMany files is not required but recommended for clarity.

## Running RunMany From Python

RunMany can be imported and used from Python as follows:

```py
from runmany import runmany, runmanys

# Run to stdout
runmany('path/to/myfile.many', 'path/to/mysettings.json')  # settings JSON is always optional

# Run to output file
runmany('path/to/myfile.many', 'path/to/mysettings.json', 'path/to/myoutput.txt')

# Run to file object
with open('path/to/myoutput.txt', 'w') as output_file:
    runmany('path/to/myfile.many', 'path/to/mysettings.json', output_file)

# Run to string
output_string = runmanys('path/to/myfile.many', 'path/to/mysettings.json')
print(output_string)
```

In both `runmany.runmany` and `runmany.runmanys` functions, `from_string=True` will make the .many file argument be
interpreted as a string instead of a file path, and the settings JSON argument may be given as a path to the
.json file or a JSON-like Python dictionary, or `None` to provide no settings. As with running from the command line,
providing settings here means all settings embedded in the .many file are ignored.

The function `runmany.cmdline`, which takes a list of command line arguments,
is also present as an alternative to using the command line directly.

# .many Syntax

The .many file format is what RunMany expects when given a file to run.

Principally, a .many file consists of sections that each contain one or more snippets. A section starts with an
unindented header line such as `Python:` or `Stdin for Python:`,
then the content of the first snippet is what appears after the colon and on indented lines below.
Additional snippets may be added to the section with an unindented
`Also:` header, and a section ends when a new one starts or an unindented `End.` or the end of the file is reached.

A .many file runs from top to bottom, executing sections and snippets in the order they are encountered. Notably,
a .many file will run regardless of if it has syntax errors or not. Any invalid syntax will be ignored and mentioned
in an error message.

In the example .many file below, the `Stdin for Python:` section has two snippets, `bar` and `baz`, and they become the
standard input for the Python program in the `Python:` section, which has one snippet `print('foo' + input())`.
Running this file runs the Python program twice, once for `bar` and once for `baz`, giving the respective outputs
`foobar` and `foobaz`.

```text
Stdin for Python:
    bar
Also:
    baz
End.

Python:
    print('foo' + input())
End.
```

Read on for specifics about all .many file syntax, or check out
[syntax.many](https://github.com/discretegames/runmany/blob/main/examples/syntax.many)
which has examples of all syntax as well.

## Syntax Specifics

---

### Comments

`%` at the very start of a line makes a comment until the end of the line.  
`%%%` anywhere in a line makes a comment until the end of the line unless the `"keep_comments"` setting is true.

```text
% this is a comment
    %%% this is also a comment
```

There are no block comments.

---

### Sections & Snippets

As mentioned, a .many file consists of sections that start with a header and contain snippets.
There are four types of sections:

- [Code sections](https://github.com/discretegames/runmany#code-section)
with the header `<language>:` or `<language1>, <language2>, ...:`
- [Argv sections](https://github.com/discretegames/runmany#argv-section)
with the header `Argv:` or `Argv for <language1>, <language2>, ...:`
- [Stdin sections](https://github.com/discretegames/runmany#stdin-section)
with the header `Stdin:` or `Stdin for <language1>, <language2>, ...:`
- [Settings sections](https://github.com/discretegames/runmany#settings-section) with the header `Settings:`

All but the settings section can have a comma separated list of the languages it applies to in the header.
These languages, once stripped of whitespace, must match the `"name"` keys of the languages in the
[settings](https://github.com/discretegames/runmany#settings) JSON,
but are not case sensitive. (Keywords like "Argv" and "Stdin" *are* case sensitive. Custom languages should not use
RunMany keywords as names nor contain the characters `,:%!@`.)

The header `Also:` is used to add snippets to a section and `End.` can optionally be used to end a section.

The content of a snippet is the text after any whitespace after the colon (`:`) in the snippet header,
plus all the lines below that are indented with a single tab or 4 spaces (with these indents removed),
until the next header or `End.` or end of file.

So this code section

```text
Python: import math
    print(math.pi)
Also: print('pie')
    print('cake')
```

has two snippets whose contents are:

```py
import math
print(math.pi)
```

```py
print('pie')
print('cake')
```

Blank lines above or below sections are only for readability and not required.
Uncommented code outside of sections is invalid.

---

### Code Section

A code section starts right out with a comma separated list of languages
and its snippet contents are the programs to run in those languages.

One language in the comma separated list is almost always sufficient unless you are writing
[polyglots](<https://en.wikipedia.org/wiki/Polyglot_(computing)>),

```text
JavaScript:
    console.log('Some code that will be run in JavaScript.')

Python, Python 2:
    print('Some code that will be run in Python 3 then Python 2.')
Also:
    print('Some more code that will be run in Python 3 then Python 2.')
```

`Also:` snippet headers in code sections are shorthand for repeating the section header.

---

### Argv Section

Argv is the argument vector, aka the command line arguments sent to programs.

An argv section can either start `Argv:` to apply to all languages, or `Argv for <language1>, <language2>, ...:` to
apply to the languages in the comma separated list. Either way overwrites any previous argv set for those languages.

Each snippet in an argv section is a separate argv that will be sent in turn to the programs of the languages
the section applies to. This makes it easy to test many argvs at once.

```text
Argv: argv sent to all languages

Argv for Python: 1
Also: 2
Also: 3

Python:
    import sys
    print(sys.argv[1])
```

This .many code will run the Python program three times with argv `1` then `2` then `3`.

For argv to work the [`$argv` placeholder](https://github.com/discretegames/runmany#command-format)
must be placed properly into the command of the language.

---

### Stdin Section

Almost exactly like an argv section but for the standard input stream users normally type text into.

An stdin section can either start `Stdin:` to apply to all languages, or `Stdin for <language1>, <language2>, ...:` to
apply to the languages in the comma separated list. Either way overwrites any previous stdin set for those languages.

Each snippet in a stdin section is a separate stdin that will be sent in turn to the programs of the languages
the section applies to. This makes it easy to test many stdins at once.

```text
Stdin: stdin sent to all languages

Stdin for Python: A
Also: B
Also: C

Python:
    print(input())
```

This .many code will run the Python program three times with stdin `A` then `B` then `C`.

When multiple argvs and stdins apply to one language, all possible combinations of every argv and every stdin
are sent to programs of that language.

---

### Settings Section

A settings section starts with `Settings:` and allows embedding a
[settings](https://github.com/discretegames/runmany#settings)
JSON in a .many file, which is used until another settings section is encountered.

These embedded settings are only used when settings were not specifically provided when runmany was called.
Any missing settings default to their values in
[default_settings.json](https://github.com/discretegames/runmany/blob/main/src/runmany/default_settings.json).

```text
Settings:
    { "show_code": true }
Python:
    print('this Python code will now be shown as part of the output')
```

A JSON string of the path to a settings file can also be used, like `Settings: "path/to/mysettings.json"`.

`Also:` snippet headers in settings sections are shorthand for repeating the section header.
So they don't serve much purpose since they immediately overwrite the previous settings.

---

### Disabled Sections & Snippets

Putting `!!` at the start of a section header disables the entire section and all its snippets.

Putting `!` at the start of a snippet header disables that snippet.

```text
!!Python:
    print('this is disabled')
Also:
    print('this is also disabled')

!Python:
    print('this is disabled')
Also:
    print('this is not disabled')
!Also:
    print('this is disabled')
```

### Solo Sections & Snippets

If any section headers start with `@@` then only those sections are run, similar to a "solo" checkbox in
audio/video editing software.

If any snippet headers within a section start with `@` then only those snippets are run when the section runs.

```text
@@@Python:
    print('this is run')
Also:
    print('this is not run')
@Also:
    print('this is run')

Python:
    print('this is not run')
@Also:
    print('this is also not run')
```

Note how the first line has three `@@@`, two to solo the section and another to solo its first snippet.

---

### Start & Stop

Everything before the last `START:` at the start of a line by itself in a .many file is ignored.

Everything after the first `STOP.` at the start of a line by itself in a .many file is ignored.

So only the JavaScript section of this .many file is run:

```text
Python: print('unseen')
START:
JavaScript: console.log('seen')
STOP.
Python: print('unseen')
```

There should only be up to one `START:` and one `STOP.` in a .many file.

---

# Settings

RunMany's setting are defined by a [JSON](https://www.json.org/) file that can be
[provided when runmany is called](https://github.com/discretegames/runmany#usage)
or [directly embedded in a .many file](https://github.com/discretegames/runmany#settings-section).

The settings JSON defines what languages RunMany can run and how it will run them.
It also defines how the RunMany output will be formatted.

The file [default_settings.json](https://github.com/discretegames/runmany/blob/main/src/runmany/default_settings.json)
holds the default values for all settings.
These defaults are automatically used if not present in a provided or embedded settings JSON.

## Customizing Languages

Most settings are simple flags or values that can be set in the base settings JSON object to apply them globally
(see [List of Settings](https://github.com/discretegames/runmany#list-of-settings))
but four special keys in the JSON are used to customize the languages RunMany can run or to add more languages.
These are `"languages"`, `"languages_windows"`, `"languages_linux"` and `"languages_mac"`
(`"languages_<os>"` will be used to refer to the last three).
They are arrays of single-level JSON objects that specify the settings for the language that
matches the `"name"` key of the object.

The `"languages_<os>"` array that matches the system OS has highest priority when determining a language's settings,
followed by the `"languages"` array, followed by the built-in `"supplied_languages_<os>"` and `"supplied_languages"`
arrays. (These `"supplied_languages..."` arrays should never be set in your settings JSON.) Languages use the settings
in the base JSON object as a final fallback.

For example, the following settings JSON sets the `"show_code"` setting (which is false by default)
to true for all languages except for Python and Python 2. It also creates a new language
"Python 3.10" that can be used in a .many file section header on Windows.

```json
{
    "show_code": true,
    "languages": [
        { "name": "Python", "show_code": false },
        { "name": "Python 2", "show_code": false }
    ],
    "languages_windows": [
        { "name": "Python 3.10", "extension": ".py", "command": "py -3.10" }
    ]
}
```

The `"name"` key is required for every object in a languages array, and the `"command"` and `"extension"` keys
should always be provided for new custom languages. Not every setting makes sense to apply on a per-language basis
though. For example, `"show_equal"` applies to the run of the .many file as a whole, so it only makes sense in the
base JSON object.

## List of Settings

All settings described and whether or not they can be overridden on a per-language basis in the
`"languages"` and `"languages_<os>"` array objects:

| JSON Key          | Type   | Default            | Overridable | Description |
| ----------------- | ------ | ------------------ | ----------- | ----------- |
| `"command"`       | string | `"echo NOCOMMAND"` | yes         | The console command to run a language, following the [command format](https://github.com/discretegames/runmany#command-format).
| `"extension"`     | string | `""`               | yes         | The file extension of a language, including the dot.
| `"timeout"`       | float  | `10.0`             | yes         | The time limit of each program in seconds.
| `"stderr"`        | string | `"smart"`          | yes         | `"yes"`/`true` to combine program stderr with stdout. `"no"`/`false` to hide program stderr. `"smart"`/`null` to only show stderr when programs have non-zero exit codes.
| `"spacing"`       | int    | `1`                | yes         | The number of blank lines to add after each run.
| `"newline"`       | string | `"\n"`             | yes         | What newlines are replaced with in code, argv, and stdin snippet content. Or `null` for the OS default.
| `"tab"`           | string | `"\t"`             | yes         | What the tab character is replaced with in code, argv, and stdin snippet content.
| `"minimalist"`    | bool   | `false`            | no          | Whether to display all output in a minimal format where the dividers, code, argv, and stdin are not shown.
| `"run_blanks"`    | bool   | `false`            | no          | Whether blank snippets that consist purely of whitespace are run or ignored.
| `"keep_comments"` | bool   | `false`            | no          | Whether `%%%` comments are kept as snippet contents and thus not treated as comments.
| `"show_time"`     | bool   | `false`            | yes         | Whether the execution time is shown.
| `"show_command"`  | bool   | `false`            | yes         | Whether the command used to run each program is shown. Useful for debugging commands for new languages.
| `"show_code"`     | bool   | `false`            | yes         | Whether the source code of the program is shown.
| `"show_argv"`     | bool   | `true`             | yes         | Whether the argv for the program is shown (when present).
| `"show_stdin"`    | bool   | `true`             | yes         | Whether the stdin for the program is shown (when present).
| `"show_output"`   | bool   | `true`             | yes         | Whether the output for the program is shown. This includes the stdout, and, depending on `"stderr"`, the stderr.
| `"show_runs"`     | bool   | `true`             | no          | Whether the list of runs is shown. This is usually the bulk of the output.
| `"show_stats"`    | bool   | `true`             | no          | Whether the success and failure counts are shown after everything has run.
| `"show_equal"`    | bool   | `true`             | no          | Whether the matching stdouts are compared and grouped after everything has run.
| `"show_errors"`   | bool   | `true`             | no          | Whether RunMany errors like `%%% RunMany Error: ... %%%` are sent to stderr or silenced.
| `"strip_argv"`    | string | `"smart"`          | no          | `"yes"`/`true` to strip the snippet content of leading and trailing whitespace. `"no"`/`false` to keep the snippet content as is. `"smart"`/`null` to join all the lines in the snippet together with spaces as if they were on one line.
| `"strip_stdin"`   | string | `"smart"`          | no          | `"yes"`/`true` to strip the start and end of the snippet of whitespace-only lines. `"no"`/`false` to keep the snippet content as is. `"smart"`/`null` to do the same as `"yes"`/`true` but also append a single newline.
| `"strip_code"`    | string | `"smart"`          | yes         | `"yes"`/`true` to strip the start and end of the snippet of whitespace-only lines. `"no"`/`false` to keep the snippet content as is. `"smart"`/`null` to treat the top of the .many file as the start of the code snippet with all irrelevant parts blanked out so errors in programs report correct line numbers.
| `"strip_output"`  | string | `"no"`             | yes         | `"yes"`/`true` to strip program output of leading and trailing whitespace. `"no"`/`false` to leave program output as is. `"smart"`/`null` to strip program output of empty leading and trailing lines.

It should be mentioned that the code, argv, and stdin portions of the .many file output are stripped of empty lines
to keep things visually clean regardless of the values of `"strip_code"`, `"strip_argv"`, and `"strip_stdin"`.

## Command Format

The `"command"` key of an object in the `"languages"` or `"languages_<os>"`
array defines the terminal command that is run to execute that language.

Placeholders like `$file` and `$dir` can be used in a command to refer to the temporary file RunMany creates
for the code of each program it runs and the directory that file is stored in:

| Placeholder  | Portion of `.../dir/file.ext`   |
| ------------ | ------------------------------- |
| `$rawdir`    | `.../dir`                       |
| `$dir`       | `".../dir"`                     |
| `$rawfile`   | `.../dir/file.ext`              |
| `$file`      | `".../dir/file.ext"`            |
| `$rawbranch` | `.../dir/file`                  |
| `$branch`    | `".../dir/file"`                |
| `$name`      | `file.ext`                      |
| `$stem`      | `file`                          |
| `$ext`       | `.ext`                          |
| `$sep`       | `/` (OS specific)               |
| `$argv`      | n/a - the argv is inserted here |
| `$code`      | n/a - the raw snippet content   |

Note that some placeholders are "quoted" and some are not.
Some operating systems like Windows may have spaces in the path to temporary files so correct quoting is important.

<!-- markdownlint-disable-next-line MD038 -->
If `$` is not present anywhere in the command string, ` $file $argv` is appended to it.
For example, the command `python` is implicitly `python $file $argv`.

Check the `"supplied_languages"` array in
[default_settings.json](https://github.com/discretegames/runmany/blob/main/src/runmany/default_settings.json)
for more examples of commands.

# About

I was driven to make RunMany by my desire to learn more programming languages,combined with my annoyance that whenever
I tried I would invariably have to make a whole new project for that language, or even switch IDEs.

I plan to use it to practice solving code challenges in multiple languages from sites like
[Project Euler](https://projecteuler.net/archives).

[Check out some of my other Python packages.](https://pypi.org/user/discretegames/)
