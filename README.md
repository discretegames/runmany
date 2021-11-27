<!-- markdownlint-disable-next-line MD041 -->
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/runmany)](https://www.python.org/downloads/)
[![Test Coverage](https://raw.githubusercontent.com/discretegames/runmany/main/coverage.svg)](https://github.com/discretegames/runmany/blob/main/coverage.txt)

# [RunMany](https://pypi.org/project/runmany/)

**[Intro](https://github.com/discretegames/runmany#runmany) | [Installation](https://github.com/discretegames/runmany#installation) | [VSCode Extension](https://github.com/discretegames/vscode-extension) | [Usage](https://github.com/discretegames/runmany#usage) | [Syntax](https://github.com/discretegames/runmany#many-syntax) | [Settings](https://github.com/discretegames/runmany#settings) | [About](https://github.com/discretegames/runmany#about)**

*This readme is out of date as RunMany is being updated to v2.*

**A tool to run many programs written in many languages from one file.**

Normally to practice multiple programming languages at once you need multiple files or multiple projects,
perhaps multiple IDE's. RunMany is a tool that lets you write multiple programs in _the same_ file using
any programming languages you want, and then run them all at once.

RunMany uses ".many" as its file extension, so for example, if a file called
[`simple.many`](https://github.com/discretegames/runmany/blob/main/examples/simple.many) has the following contents:

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

Then doing `runmany simple.many` in terminal will produce
[this organized output](https://github.com/discretegames/runmany/blob/main/examples/simple_output.txt)
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

- Chrestomathy - Writing identically behaving programs in many languages, like on [Rosetta Code](http://www.rosettacode.org/wiki/Rosetta_Code).
    ([example](https://github.com/discretegames/runmany/blob/main/examples/helloworld.many)/[output](https://github.com/discretegames/runmany/blob/main/examples/helloworld_output.txt))
- Performance Testing - Timing different implementations of a program, even across languages.
    ([example](https://github.com/discretegames/runmany/blob/main/examples/primes.many)/[output](https://github.com/discretegames/runmany/blob/main/examples/primes_output.txt))
- Input Testing - Easily giving many combinations of argv or stdin to programs.
    ([example](https://github.com/discretegames/runmany/blob/main/examples/inputs.many)/[output](https://github.com/discretegames/runmany/blob/main/examples/inputs_output.txt))
- Polyglots - Making esoteric code that can be executed in multiple languages at once.
    ([example](https://github.com/discretegames/runmany/blob/main/examples/polyglot.many)/[output](https://github.com/discretegames/runmany/blob/main/examples/polyglot_output.txt))

Overall RunMany is hopefully a useful tool for anyone who wants to play with multiple programming languages at once.

# Installation

Make sure you have [Python](https://www.python.org/downloads/) version 3.6 or above installed then run

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
because RunMany uses their interpreters/compilers behind the scenes to actually run the programs.

RunMany has built-in support for the following languages:

> Ada, Bash, Batch, C, C#, C++, Dart, Fortran, Go, Groovy, Haskell, Java, JavaScript, Julia, Kotlin, Lisp, Lua, MIPS,
Pascal, Perl, PHP, PowerShell, Print, Python, Python 2, R, Racket, Ruby, Rust, Scala, TypeScript, VBScript, and Visual Basic

Meaning, if you already have one of these languages installed,
there's a good chance it will work in RunMany automatically.
(`Print` is a special built-in language that simply prints the code content to stdout.)

There are ways to add custom languages and change the behavior of built-in languages, and even make them different on
different operating systems. For more info see the `"languages"` and `"languages_<os>"` JSON keys in
[Settings](https://github.com/discretegames/runmany#settings).

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
that run interpreters/compilers of other programming languages.

RunMany is now in version 2 with improved .many file syntax and more settings.
The old 1.0.3 version is still available [on PyPI](https://pypi.org/project/runmany/1.0.3/).

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

When a settings file is provided on command line, any `Settings:` sections embedded in the input file are ignored.
If neither are present, or for any missing settings,
[default_settings.json](https://github.com/discretegames/runmany/blob/main/src/runmany/default_settings.json)
is used as a fallback. See more info in [Settings](https://github.com/discretegames/runmany#settings).

For some examples of .many files and their output check
[the examples folder on GitHub](https://github.com/discretegames/runmany/tree/main/examples).
(The .many extension for RunMany files is not required but recommended for clarity.)

## Running RunMany From Python

RunMany can be imported and used from Python as follows:

```py
from runmany import runmany, runmanys

# Run to stdout
runmany('path/to/myfile.many', 'path/to/mysettings.json')  # settings JSON is always optional and can be None

# Run to output file
runmany('path/to/myfile.many', 'path/to/mysettings.json', 'path/to/myoutput.txt')

# Run to file object
with open('myoutput.txt', 'w') as file:
    runmany('path/to/myfile.many', 'path/to/mysettings.json', file)

# Run to string
output_string = runmanys('path/to/myfile.many', 'path/to/mysettings.json')
print(output_string)
```

In both `runmany.runmany` and `runmany.runmanys` functions, `from_string=True` will make the .many file argument be
interpreted as a string instead of a file path, and the settings JSON argument may be given as a path to the
.json file or a JSON-like Python dictionary, or `None` to provide no settings. As with running from the command line,
providing settings here means all settings embedded in the .many file are ignored.

The function `runmany.cmdline`, which takes a list of command line arguments, is also present as an alternative to using the command line directly.

# .many Syntax

The .many file format is what RunMany expects when given a file to run. (Though, of course, ".many" is not required as an extension.)

Principally, a .many file consists of unindented lines which are section headers that define the languages and context for the lines indented below them. Languages are given as a comma separated list and the 3 contexts are argv, stdin, and code. Section headers end with a colon.

```text
Argv for Python, JavaScript:
    foo
Stdin for Python:
    bar
Python:
    import sys
    print(sys.argv[1] + input())  # will be "foobar"
JavaScript:
    console.log(process.argv[2])  // will be "foo"
```

The keywords `Argv` and `Stdin` are used to define the argument vector and standard input for a set of languages. Otherwise the section is assumed to be code.

So the RunMany program above will send "foo" to Python and JavaScript on argv, and "bar" to Python on stdin when it runs each language's code.

Importantly, a .many file always runs from top to bottom [just-in-time](https://en.wikipedia.org/wiki/Just-in-time_compilation),
that is, the top lines will run normally even if the bottom lines are invalid syntax.
For this reason, argv and stdin sections only apply to code sections that come after them.

Those are the essentials but read on for more details and nuance about the syntax of .many files. Notably the [Also Section](https://github.com/discretegames/runmany#also-section) and [hardcoded settings](https://github.com/discretegames/runmany#hardcoded-settings).

Also check [syntax.many](https://github.com/discretegames/runmany/blob/main/examples/syntax.many) and the [other examples](https://github.com/discretegames/runmany/tree/main/examples) for concrete syntax samples.

## Syntax Specifics

---

### Comments

`%` at the very start of a line makes an inline comment.

```text
% this is a comment
```

There are no block comments.

---

### Section Syntax

A .many file can be split up into sections, each of which has an unindented header line that ends in a colon (`:`),
and a potentially multiline string of content that can appear after the colon and on indented lines below the header.
Each indent must be either a single tab or 4 spaces and the indents do not end up as part of the section content.

Any whitespace just after the colon of the section header is ignored, so this is a working Code Section:

```text
Python: import math
    print(math.pi)
```

As it corresponds to the Python program:

```py
import math
print(math.pi)
```

Blank lines above or below sections are only for readability and not required.

As detailed below, only a few types of sections exist and some require comma (`,`) separated language lists in their headers.
Language names are stripped of whitespace and matched to corresponding `"name"` keys in the languages arrays of the [settings JSON](https://github.com/discretegames/runmany#settings).

Language names are not case-sensitive (`Python` is the same as `python`)
but other keywords like `Argv`, `Stdin`, `for`, `Also`, and `Exit` are.

Language names cannot contain `,` or `:` and to be safe they should not start with `Argv`, `Stdin`, `Also`, `Exit`, or `!`.

---

### Code Section

A Code Section starts right out with a comma separated list of languages and its content is the program to be run in those languages.

One language in the list is almost always sufficient unless you are writing [polyglots](<https://en.wikipedia.org/wiki/Polyglot_(computing)>),

```text
JavaScript:
    console.log('This is some code that will be run in JS.')
Python, Python 2:
    print('This is some code that will be run in Python 3 and then Python 2.')
```

---

### Argv Section

An Argv Section can either start `Argv:` to apply to all languages, or `Argv for Language1, Language2, ...:` to apply to the listed languages.
Either way overwrites any previous argv set for those languages, but [Also Sections](https://github.com/discretegames/runmany#also-section)
can be used to supply a series of argvs.

The Argv Section's content is stripped of newlines and sent as the argument vector to all the subsequent programs in Code Sections it applies to.

```text
Argv:
    argv sent to all languages
Argv for Python, JavaScript:
    argv specifically sent to Python and Javascript
```

For argv to work the [`$argv` placeholder](https://github.com/discretegames/runmany#command-format) must be placed properly into the command of the language.

---

### Stdin Section

Almost exactly like an Argv Section but for stdin.

A Stdin Section can either start `Stdin:` to apply to all languages, or `Stdin for Language1, Language2, ...:` to apply to the listed languages.
Either way overwrites any previous stdin set for those languages, but [Also Sections](https://github.com/discretegames/runmany#also-section)
can be used to supply a series of stdins.

The Stdin Section's content is stripped of trailing newlines except one and sent as the standard input stream to all the subsequent programs in Code Sections it applies to.

```text
Stdin:
    stdin sent to all languages
Stdin for Python, JavaScript:
    stdin specifically sent to Python and Javascript
```

When a program expects stdin but there is no Stdin Section to give it, the stdin can be typed into the console normally.

---

### Also Section

An Also Section starts with `Also:` (with no language list) and is a way to add a series of argvs or stdins to run,
or to avoid repeating a Code Section header. It cannot be the first section in the file because it needs to attach to the Code, Stdin, or Argv Section above it.

When below an Argv Section or Stdin Section, an Also Section adds an additional input
to the list of argvs or stdins to run when applicable Code Sections are encountered.

For example, the final Python program here is run 6 times for all the combinations of argvs and stdins that apply to it
(`1A 1B 2A 2B 3A 3B`):

```text
Argv: 1
Also: 2
Also: 3

Stdin: A
Also:  B

Python:
    import sys
    print(sys.argv[1] + input())
```

This is the real power of the Also Section -- giving multiple argvs and stdins to a program without repeating code.
[Another example](https://github.com/discretegames/runmany/blob/main/examples/inputs.many) with [output](https://github.com/discretegames/runmany/blob/main/examples/inputs_output.txt).

When below a Code Section, an Also Section is simply shorthand for repeating the Code Section's header.

For example, `Also:` here behaves exactly the same as `Python, Python 2:` would:

```text
Python, Python 2:
    print(123)
Also:
    print(456)
Also:
    print(789)
```

---

### Disabling Sections

Putting `!` at the very start of any section header will disable that section and any Also Sections attached to it.

```text
!Python:
    # this is disabled
Also:
    # this is effectively disabled too
!Also:
    # this is disabled in two ways
```

---

### Hardcoded Settings

A [settings JSON](https://github.com/discretegames/runmany#settings) may be placed, indented, before the first section in a .many file. It is only used if a custom setting JSON is not otherwise provided as an argument, and only for the .many file it is in.
As with section content, the indents may be either single tabs or 4 spaces.

```text
    {
        "show_time": true,
        "show_command": true
    }
Python:
    print('The time and command will now be shown.')
```

---

### Exit Command

`Exit.` at the very start of a line by itself will stop RunMany as if the file ended there.

```text
Exit.
% nothing from here on will be run
```

---

# Settings

The settings JSON defines what languages RunMany can run and how it will run them. It also defines how the RunMany output will be formatted.

As mentioned, [default_settings.json](https://github.com/discretegames/runmany/blob/main/src/runmany/default_settings.json)
holds the default values for all settings which are automatically used if not otherwise present in a provided or hardcoded JSON.

Most settings are simple flags or values that can be set in the base settings JSON object. See [List of Settings](https://github.com/discretegames/runmany#list-of-settings) below.

The setting to add a custom language is the `"languages"` key which maps to an array of JSON objects we'll call language objects. Each language object must have a `"name"`
string to identify it and a `"command"` string to run it (see [command format](https://github.com/discretegames/runmany#command-format)).
However, objects in `"languages"` with a matching `"name"` in the `"default_languages"` array will automatically inherit its other values, such as `"command"` and `"ext"`.
Most settings that can be set in the base settings JSON object are also inherited by the language objects and can be overridden.

For example, a settings JSON of

```json
{
    "languages": [{ "name": "Rust", "timeout": 5.0 }],
    "show_code": true
}
```

will make Rust programs have a 5 second time limit rather than the default of 10, and `"command"` does not need to be present because Rust is already in the built-in `"default_languages"` array. The `"show_code": true` in the base object makes it so _all_ languages in the RunMany output will show their code.

You should not have to set `"default_languages"` in your custom settings JSON (though technically you can). Only set `"languages"`.

## List of Settings

All settings described and whether or not they they can be overridden in a language object in the `"languages"` array:

| JSON Key         | Type   | Default  | Overridable | Description                                                                                                                                                                                                                   |
| ---------------- | ------ | -------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `"timeout"`      | float  | `10.0`   | yes         | The time limit of each program in seconds.                                                                                                                                                                                    |
| `"stderr"`       | string | `"nzec"` | yes         | `"always"` or `true` to always combine program stderr streams with stdout. `"never"` or `false` to always hide program stderr streams. `"nzec"` or `null` to only show stderr streams when programs have non-zero exit codes. |
| `"ext"`          | string | `""`     | yes         | The file extension of a language including the dot. Best to always define in the language object.                                                                                                                             |
| `"spacing"`      | int    | `1`      | yes         | The number of blank lines to add after each run. Note that trailing newlines are not stripped from stdouts.                                                                                                                   |
| `"show_time"`    | bool   | `false`  | yes         | Whether the execution time of each program is shown.                                                                                                                                                                          |
| `"show_command"` | bool   | `false`  | yes         | Whether the command used to run each program is shown. Useful for debugging command setup for new languages.                                                                                                                  |
| `"show_code"`    | bool   | `false`  | yes         | Whether the source code of the program is shown.                                                                                                                                                                              |
| `"show_argv"`    | bool   | `true`   | yes         | Whether the argv for the program is shown (when present and non-empty).                                                                                                                                                       |
| `"show_stdin"`   | bool   | `true`   | yes         | Whether the stdin for the program is shown (when present and not all empty lines).                                                                                                                                            |
| `"show_output"`  | bool   | `true`   | yes         | Whether the output for the program is shown. This includes the stdout, and, depending on the `"stderr"` setting, the stderr.                                                                                                  |
| `"show_errors"`  | bool   | `true`   | no          | Whether RunMany errors like `!!!\| RunMany Error: ... \|!!!` are sent to stderr or silenced.                                                                                                                                  |
| `"show_runs"`    | bool   | `true`   | no          | Whether the list of runs is shown. This is usually the bulk of the output.                                                                                                                                                    |
| `"show_stats"`   | bool   | `true`   | no          | Whether the success and failure counts are shown after everything has run.                                                                                                                                                    |
| `"show_equal"`   | bool   | `true`   | no          | Whether the matching stdouts are compared and grouped after everything has run.                                                                                                                                               |

## Command Format

The `"command"` key of a language object in the `"languages"` array defines the terminal command that is run to execute the language.

Placeholders like `$file` and `$dir` are used in a command to refer to the temporary file RunMany creates for the code of each program it runs, or the directory that file is stored in:

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

Note that some placeholders are "quoted" and some are not. Some operating systems like Windows may have spaces in the path to temporary files so correct quoting is important.

<!-- markdownlint-disable-next-line MD038 -->
If `$` is not present anywhere in the command string, ` $file $argv` is appended to it.
For example, the command `python` is implicitly `python $file $argv`.

Check the `"default_languages"` array in [default_settings.json](https://github.com/discretegames/runmany/blob/main/src/runmany/default_settings.json) for more examples of commands.

# About

I was driven to make RunMany by my desire to learn more programming languages combined with my annoyance that whenever I tried I would invariably have to make a whole new project for that language, or even switch IDEs.

I plan to use it to practice solving code challenges in multiple languages from code challenge websites.

[Check out some of my other Python packages.](https://pypi.org/user/discretegames/)
