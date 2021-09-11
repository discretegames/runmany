<!-- markdownlint-disable-next-line MD041 -->
[![PyPI Version](https://badge.fury.io/py/runmany.svg)](https://badge.fury.io/py/runmany)
 [![Test Coverage](https://raw.githubusercontent.com/discretegames/runmany/main/coverage.svg)](https://github.com/discretegames/runmany/blob/main/coverage.txt)
 [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/runmany)](https://www.python.org/downloads/)

# [RunMany](https://pypi.org/project/runmany/)

**[Intro](https://github.com/discretegames/runmany#runmany) | [Installation](https://github.com/discretegames/runmany#installation-supports-python-36) | [Usage](https://github.com/discretegames/runmany#usage) | [Syntax](https://github.com/discretegames/runmany#many-syntax) | [Settings](https://github.com/discretegames/runmany#settings-json) | [About](https://github.com/discretegames/runmany#about)**

**A tool to run many programs written in many languages from one file.**

Suppose you want to practice multiple programming languages at once. Normally you'd have to juggle multiple files or multiple projects, perhaps multiple IDEs. RunMany lets you write multiple programs in *the same* file using any programming languages you like, and then run them all at once.

For example, give RunMany [this](https://github.com/discretegames/runmany/blob/main/examples/simple.many) simple file:

```text
Python:
    print("Hi")
JavaScript:
    console.log("Hi")
Rust:
    fn main() {
        println!("Hi");
    }
```

And it will number and run each program, giving [this](https://github.com/discretegames/runmany/blob/main/examples/simple_output.txt) output:

```text
************************************************************
1. Python
-------------------- output from line 2 --------------------
Hi


************************************************************
2. JavaScript
-------------------- output from line 4 --------------------
Hi


************************************************************
3. Rust
-------------------- output from line 6 --------------------
Hi


************************************************************
3/3 programs successfully run!
3/3 had the exact same stdout!
************************************************************
```

In general, RunMany can be used for:

- Crestomathy - Writing identically behaving programs in many languages, like on [Rosetta Code](http://www.rosettacode.org/wiki/Rosetta_Code).
 ([example](https://github.com/discretegames/runmany/blob/main/examples/helloworld.many)/[output](https://github.com/discretegames/runmany/blob/main/examples/helloworld_output.txt))
- Performance Testing - Timing different implementations of a program, even across languages.
 ([example](https://github.com/discretegames/runmany/blob/main/examples/primes.many)/[output](https://github.com/discretegames/runmany/blob/main/examples/primes_output.txt))
- Input Testing - Easily giving many combinations of argv or stdin input to programs.
 ([example](https://github.com/discretegames/runmany/blob/main/examples/inputs.many)/[output](https://github.com/discretegames/runmany/blob/main/examples/inputs_output.txt))
- Polyglots - Making esoteric code that can be executed in multiple languages at once.
 ([example](https://github.com/discretegames/runmany/blob/main/examples/polyglot.many)/[output](https://github.com/discretegames/runmany/blob/main/examples/polyglot_output.txt))

# Installation (supports Python 3.6+)

```text
pip install runmany
```

[PyPI Package Page](https://pypi.org/project/runmany/) | [Bleeding edge version on TestPyPI](https://test.pypi.org/project/runmany/)

# Usage

## Running From Command Line

```text
runmany myfile.many
```

More generally:

```text
runmany [-h --help] [-j --json <settings-file>] [-o --output <output-file>] <input-file>
```

- `<input-file>` is the required .many file to run.
- `<settings-json>` is the optional .json file that defines how languages are run and how the output is formatted.
- `<output-file>` is the optional file to send the output to. When omitted output goes to stdout.

**When a settings JSON file is not provided, the hardcoded settings JSON at the top of the .many file is used. If neither is provided, or for any missing settings, [default_settings.json](https://github.com/discretegames/runmany/blob/main/runmany/default_settings.json) is used as a fallback.**

See [the examples folder](https://github.com/discretegames/runmany/tree/main/examples) for some .many files to try. Note that they were run on a Windows machine with the necessary interpreters and compilers installed.

The [default JSON](https://github.com/discretegames/runmany/blob/main/runmany/default_settings.json) has presets for a handful of languages, namely Python, Python 2, JavaScript, TypeScript, Java, Kotlin, Rust, Go, C, C++, and C#. But any of these can be overwritten and new languages can be added by populating the `"languages"` key in a custom JSON. See more details in the [Settings section.](https://github.com/discretegames/runmany#settings-json)

## Running From Python

```py
from runmany import runmany, runmany_to_s, runmany_to_f

# Run to stdout
runmany('path/to/input.many', 'path/to/settings.json') # settings JSON is always optional

# Run to output file
runmany('path/to/input.many', 'path/to/settings.json', 'path/to/output.txt')

# Run to string
string = runmany_to_s('path/to/input.many', 'path/to/settings.json')

# Run to file object
with open('output.txt', 'w') as file_obj:
    runmany_to_f(file_obj, 'path/to/input.many', 'path/to/settings.json')
```

As with the command line, the settings JSON provided takes precedence over the JSON that may be at the top of the .many file, and [default_settings.json](https://github.com/discretegames/runmany/blob/main/runmany/default_settings.json) is used as a fallback for all settings.

In each of the 3 runmany functions, the settings JSON argument may be given as a path to the .json file or a JSON-like Python dictionary.

Additionally, the .many file contents may be given as a string rather than a file path with `from_string=True`.

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

As can be guessed, the keywords `Argv` and `Stdin` are used to define the argument vector and standard input for a set of languages. Otherwise the section is assumed to be code.

So the above RunMany program will send "foo" to Python and JavaScript on argv, and "bar" to Python on stdin when it runs each language's code.

Importantly, a .many file always runs from top to bottom [just-in-time](https://en.wikipedia.org/wiki/Just-in-time_compilation),
that is, the top lines will run normally even if the bottom lines are invalid syntax.
For this reason, argv and stdin sections only apply to code sections that come after them.

Those are the essentials but read on for more details and nuance about the syntax of .many files. Notably the [also section](https://github.com/discretegames/runmany#also-section) and [hardcoding a settings JSON](https://github.com/discretegames/runmany#hardcoded-settings).

## Syntax Specifics

### Comments

`%` at the very start of a line makes an inline comment.

`/%` at the very start of a line up to a matching `%/` at the very start of another line makes a multiline comment.

```text
% this is a comment

/%
this is a block comment
%/
```

### Section Header & Content

A section is a non

A section header is an unindented line 





TODO

### Argv Section

An argv section can either start `Argv:` to apply to all languages, or `Argv for Language1, Language2, ...:` to apply to the languages in the comma separated list. Either way overwrites any previous argv set for those languages, but [also sections](https://github.com/discretegames/runmany#also-section)
can be used to supply multiple argvs at a time.

The argv section content is stripped of newlines and sent as the argument vector to all the subsequent programs of the languages it applies to.

```text
Argv:
    argv sent to all languages
Argv for Python, JavaScript:
    argv specifically sent to Python and Javascript
```

For argv to work the [`$argv` placeholder](https://github.com/discretegames/runmany#command-format) must be placed properly into the command of the language.

### Stdin Section

Almost exactly like the argv section but for stdin.

A stdin section can either start `Stdin:` to apply to all languages, or `Stdin for Language1, Language2, ...:` to apply to the languages in the comma separated list. Either way overwrites any previous stdin set for those languages, but [also sections](https://github.com/discretegames/runmany#also-section)
can be used to supply multiple stdins at a time.

The stdins section content is stripped of newlines and one trailing newline is added if it is not empty. It is then sent as the standard input  stream to all the subsequent programs of the languages it applies to.

```text
Stdin:
    stdin sent to all languages
Stdin for Python, JavaScript:
    stdin specifically sent to Python and Javascript
```

When a program expects stdin but there is no stdin section to give it, it can be typed into the console normally.

### Code Section

### Also Section

### Disabling Sections

### Hardcoded Settings

TODO

### Exit Command

`Exit.` at the very start of a line by itself (possibly with trailing whitespace) will stop RunMany as if the file ended there.

```text
Exit.
% nothing from here on will be run
```

# Settings JSON

The settings JSON defines what languages RunMany can run and how to run them. It also defines how the output will be formatted.

As mentioned, [default_settings.json](https://github.com/discretegames/runmany/blob/main/runmany/default_settings.json) holds the default values for all settings which are automatically used if not otherwise present in a provided or hardcoded JSON.

The setting to add a custom language is the `"languages"` key, which maps to a list of JSON 'language' objects, each of which must have a `"name"` string to identify it and a `"command"` string to run it (see [command format](https://github.com/discretegames/runmany#command-format)). However, objects in `"languages"` with a matching `"name"` in `"default_languages"` will automatically inherit its other values, such as `"command"` and `"ext"`. Also, most settings that exist in the base JSON object are inherited by the language objects and can be overwritten.

So, for example, a settings JSON of

```json
{ "languages": [{"name": "Rust", "timeout": 5.0 }] }
```

will make Rust programs have a 5 second time limit rather than the default of 10, and `"command"` does not need to be present because Rust is in the default `"default_languages"`.

It is advised to not set `"default_languages"` in your settings JSON file and only change `"languages"`.

## List of Settings

All settings described, and whether or not they are inherited by language objects in `"languages"`:

| JSON Key         | Type   | Default  | Inherited | Description                                                                                                                                                                                    |
| ---------------- | ------ | -------- | --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `"all_name"`     | string | `"All"`  | no        | The shorthand name that expands to all languages in a section header.                                                                                                                          |
| `"timeout"`      | float  | `10.0`   | yes       | The time limit of each program in seconds.                                                                                                                                                     |
| `"stderr"`       | string | `"nzec"` | yes       | `"always"` to always combine program stderr streams with stdout. `"never"` to always hide program stderr streams. `"nzec"` to only show stderr streams when programs have non-zero exit codes. |
| `"ext"`          | string | `""`     | yes       | The file extension of a language. Best to always define in the language object.                                                                                                                |
| `"spacing"`      | int    | `1`      | yes       | The number of blank lines to add after each run. Note that trailing newlines are not stripped from stdouts.                                                                                    |
| `"show_time"`    | bool   | `false`  | yes       | Whether the execution time of each program is shown.                                                                                                                                           |
| `"show_command"` | bool   | `false`  | yes       | Whether the command used to run each program is shown.                                                                                                                                         |
| `"show_code"`    | bool   | `false`  | yes       | Whether the source code of the program is shown.                                                                                                                                               |
| `"show_argv"`    | bool   | `true`   | yes       | Whether the argv for the program is shown (when present and non-empty).                                                                                                                        |
| `"show_stdin"`   | bool   | `true`   | yes       | Whether the stdin for the program is shown (when present and non-empty).                                                                                                                       |
| `"show_output"`  | bool   | `true`   | yes       | Whether the output for the program is shown.                                                                                                                                                   |
| `"show_errors"`  | bool   | `true`   | no        | Whether RunMany errors like `!!!\| RunMany Error: ... \|!!!` are sent to stderr or silenced.                                                                                                   |
| `"show_runs"`    | bool   | `true`   | no        | Whether the list of runs (the bulk of the output) is shown.                                                                                                                                    |
| `"show_stats"`   | bool   | `true`   | no        | Whether the success and failure counts are shown after everything has run.                                                                                                                     |
| `"show_equal"`   | bool   | `true`   | no        | Whether the matching stdouts are compared and grouped after everything has run.                                                                                                                |

## Command Format

The `"command"` key of a language object defines the terminal command that is run to execute the language.

Placeholders like `$file` and `$dir` are used in a command to refer to the temporary file RunMany creates for the code of each program it runs, or the directory that file is stored in.

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
If `$` is not present anywhere in the command string, ` $file $argv` is appended to it. For example, the command `python` is implicitly `python $file $argv`.

# About

I was driven to make RunMany by my desire to learn more programming languages combined with my annoyance that whenever I tried I would invariably have to make a whole new project for that language, or even switch IDEs.

The obvious limitation of RunMany and the .many file format is that syntax highlighting and tooling like IntelliSense doesn't work. Making a VSCode extension that can syntax highlight .many files is definitely on my radar.
