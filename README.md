<!-- markdownlint-disable-next-line MD041 -->
[![PyPI Version](https://badge.fury.io/py/run-many.svg)](https://badge.fury.io/py/run-many)
 [![Test Coverage](https://raw.githubusercontent.com/discretegames/runmany/main/coverage.svg)](https://github.com/discretegames/runmany/blob/main/coverage.txt)
 [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/run-many)](https://www.python.org/downloads/)

# [RunMany](https://pypi.org/project/run-many/)

**[Intro](https://github.com/discretegames/runmany#runmany) | [Installation](https://github.com/discretegames/runmany#installation-supports-python-36) | [Usage](https://github.com/discretegames/runmany#usage) | [Syntax](https://github.com/discretegames/runmany#many-syntax) | [Settings](https://github.com/discretegames/runmany#settings-json) | [About](https://github.com/discretegames/runmany#about)**

**A tool to run many programs written in many languages from one file.**

Suppose you want to practice multiple programming languages at once. Normally you'd have to juggle multiple files or multiple projects, perhaps multiple IDEs. RunMany lets you write multiple programs in *the same* file using any programming languages you like, and then run them all at once.

For example, given the simple file

```text
~~~| Python |~~~
print("Hi")
~~~| JavaScript |~~~
console.log("Hi")
~~~| Rust |~~~
fn main() { println!("Hi"); }
```

RunMany will number and run each program

```text
------------------------------------------------------------------------------------------
RunMany Result
------------------------------------------------------------------------------------------

1. Python
-------------------------- output --------------------------
Hi

2. JavaScript
-------------------------- output --------------------------
Hi

3. Rust
-------------------------- output --------------------------
Hi

------------------------------------------------------------------------------------------
3/3 programs successfully run!
3/3 had the exact same stdout!
------------------------------------------------------------------------------------------
```

In general RunMany can be used for:

- Crestomathy - Writing programs that do the same thing in many languages, like on
 [Rosetta Code](http://www.rosettacode.org/wiki/Rosetta_Code).
 ([example](https://github.com/discretegames/runmany/blob/main/examples/helloworld.many)/[output](https://github.com/discretegames/runmany/blob/main/examples/helloworld_output.txt))
- Performance Testing - Timing different implementations of a program, even across languages.
 ([example](https://github.com/discretegames/runmany/blob/main/examples/primes.many)/[output](https://github.com/discretegames/runmany/blob/main/examples/primes_output.txt))
- Input Testing - Easily giving many combinations of argv or stdin input to programs.
 ([example](https://github.com/discretegames/runmany/blob/main/examples/inputs.many)/[output](https://github.com/discretegames/runmany/blob/main/examples/inputs_output.txt))
- Creating Polyglots - Esoteric programs that can be executed in multiple languages.
 ([example](https://github.com/discretegames/runmany/blob/main/examples/polyglot.many)/[output](https://github.com/discretegames/runmany/blob/main/examples/polyglot_output.txt))

# Installation (supports Python 3.6+)

```text
pip install run-many
```

[PyPI Package Page](https://pypi.org/project/run-many/) | [Bleeding edge version on TestPyPI](https://test.pypi.org/project/run-many/)

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

By default, output goes to stdout and [default_settings.json](https://github.com/discretegames/runmany/blob/main/run_many/default_settings.json) is used as a fallback when a custom settings JSON is not provided or is missing any settings.

See [the examples folder](https://github.com/discretegames/runmany/tree/main/examples) for some .many files to try. Note that they were run on a Windows machine with the necessary interpreters and compilers installed.

The default JSON has [presets](https://github.com/discretegames/runmany/blob/main/run_many/default_settings.json#L18) for a handful of languages, namely Python, Python 2, JavaScript, TypeScript, Java, Kotlin, Rust, Go, C, C++, and C#. But any of these can be overwritten and new languages can be added by populating the `"languages"` key in a custom JSON. [More details below.](https://github.com/discretegames/runmany#settings-json)

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

The .many file format is what RunMany expects when given a file to run. Though, of course, ".many" is not required as an extension. Since .many files may contain syntax from arbitrary programming languages, a small, unique set of syntax was required to demarcate the various parts.

## Comments and EOF Marker

Though not crucial, comments and a way to prematurely exit are provided for convenience as part of .many file syntax.

Any line in a .many file starting with `%%%|` and ending `|%%%` (possibly with trailing whitespace) is considered a comment and is completely ignored.

```test
%%%| this is a comment |%%%
```

The line `%%%|%%%` alone (possibly with trailing whitespace) is considered an end-of-file marker, and everything after it in the entire file is ignored. `!` may be put before it, e.g. `!%%%|%%%`, to disable the marker.

## Sections & Delimiters

Aside from comments and the EOF marker, a .many file can be split into a number of sections, each of which occupies its own contiguous block of lines and is headed by a section delimiter.

A section delimiter must reside on its own line that has no leading whitespace, but may have trailing whitespace.

Putting `!` at the front of any section delimiter disables it and its entire section until the next delimiter.

The part before the very first delimiter in a .many file is treated as a comment area and gets copied to the prologue part of the output. Otherwise, lines that are not section delimiters (nor comments or EOF markers) are treated as part of the section content.

**There are 6 types of section delimiters:**

1. Code Header: `~~~| language1 | language2 | language3 | ... |~~~`
   - A `|` separated list of languages, (though usually just one suffices) starting `~~~|` and ending `|~~~`.  
   - The section content is treated as code that will be run in each language in the list in turn.
   - The language names must match language names in the settings JSON which defines how they are run.

2. Code List: `~~~|~~~`
   - Expects to appear after a Code Header section or another Code List section.
   - Is merely shorthand for exactly repeating the previous Code Header delimiter.

3. Argv Header: `@@@| language1 | language2 | language3 | ... |@@@`
   - A `|` separated list of languages, starting `@@@|` and ending `|@@@` (`@` for *a*rgv).
   - The section content is stripped of newlines and will be used as the command line arguments for the listed languages in any following code sections.
   - Overwrites any previous Argv Header and Argv List sections for the listed languages.

4. Argv List: `@@@|@@@`
   - Expects to appear after an Argv Header section or another Argv List section.
   - The section content is stripped of newlines and added to the list of successive argv inputs to give to the languages listed in the previous Argv Header.
   - In this way, multiple argv inputs may be tested at once without code duplication.

5. Stdin Header: `$$$| language1 | language2 | language3 | ... |$$$`
   - A `|` separated list of languages, starting `$$$|` and ending `|$$$` (`$` for *s*tdin).
   - The section content is stripped of newlines (except one left trailing) and will be used as the stdin for the listed languages in any following code sections.
   - Overwrites any previous Stdin Header and Stdin List sections for the listed languages.

6. Stdin List: `$$$|$$$`
   - Expects to appear after a Stdin Header section or another Stdin List section.
   - The section content is stripped of newlines (except one left trailing) and added to the list of successive stdin inputs to give to the languages listed in the previous Stdin Header.
   - In this way, multiple stdin inputs may be tested at once without code duplication.

The language names in the Code Header, Argv Header, and Stdin Header are always stripped of whitespace and made lowercase before checking if they match a language defined in the settings JSON. The special keyword `All` (which [can be changed](https://github.com/discretegames/runmany#list-of-settings)) can be used as a language name and it will auto-expand to all the languages defined in the settings JSON. This is useful for giving the same argv or stdin to all programs.

Blank lines around section delimiters are only for readability and not required.

## Syntax Example

This file consists of one enabled Python program that reads from stdin and one JavaScript program that reads from argv.

```text
prologue comment area

$$$| Python |$$$
Alice
$$$|$$$
Bob
$$$|$$$
Charlie

!~~~| Python |~~~
print('this section is disabled with !')

~~~| Python |~~~
%%%| this line is a .many file comment |%%%
print(f'Hello, {input()}.')

@@@| All |@@@
--flag

~~~| JavaScript |~~~
console.log(`The arg was '${process.argv[2]}'`)

%%%|%%%
~~~| Python |~~~
print('this section is after the EOf marker')
```

The output first has all the results of running the Python program on the `$$$|$$$` separated stdins, then the result of JavaScript program given its single argv.

```text
------------------------------------------------------------------------------------------
RunMany Result
prologue comment area
------------------------------------------------------------------------------------------


1. Python
--------------------- stdin at line 4 ----------------------
Alice
-------------------------- output --------------------------
Hello, Alice.


2. Python
--------------------- stdin at line 6 ----------------------
Bob
-------------------------- output --------------------------
Hello, Bob.


3. Python
--------------------- stdin at line 8 ----------------------
Charlie
-------------------------- output --------------------------
Hello, Charlie.


4. JavaScript
--------------------- argv at line 18 ----------------------
--flag
-------------------------- output --------------------------
The arg was '--flag'


------------------------------------------------------------------------------------------
4/4 programs successfully run!
1/4 had the exact same stdout. Equal runs grouped: [1] [2] [3] [4]
------------------------------------------------------------------------------------------
```

# Settings JSON

The settings JSON defines what languages RunMany can run and how to run them. It also defines how the output will be formatted.

As mentioned, [default_settings.json](https://github.com/discretegames/runmany/blob/main/run_many/default_settings.json) holds the default values for all settings which are automatically used if not present in the provided settings JSON, or if none is provided.

The setting to add a custom language is the `"languages"` key, which maps to a list of JSON 'language' objects, each of which must have a `"name"` string to identify it and a `"command"` string to run it (see [command format](https://github.com/discretegames/runmany#command-format)). However, objects in `"languages"` with a matching `"name"` in `"default_languages"` will automatically inherit its other values, such as `"command"` and `"ext"`. Also, most settings that exist in the base JSON object are inherited by the language objects and can be overwritten.

So, for example, a settings JSON of

```json
{ "languages": [{"name": "Rust", "timeout": 5.0 }] }
```

will make Rust programs have a 5 second time limit rather than the default of 10, and `"command"` does not need to be present because Rust is in the default `"default_languages"`.

It is advised to not set `"default_languages"` in your settings JSON file and only change `"languages"`.

## List of Settings

All settings described, and whether or not they are inherited by language objects in `"languages"`.

| JSON Key          | Type   | Default  | Inherited | Description                                                                                                                                                                                    |
| ----------------- | ------ | -------- | --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `"all_name"`      | string | `"All"`  | no        | The shorthand name that expands to all languages in a section header.                                                                                                                          |
| `"check_equal"`   | bool   | `true`   | no        | Whether the second line of the epilogue that checks stdout equality is shown.                                                                                                                  |
| `"timeout"`       | float  | `10.0`   | yes       | The time limit of each program in seconds.                                                                                                                                                     |
| `"stderr"`        | string | `"nzec"` | yes       | `"always"` to always combine program stderr streams with stdout. `"never"` to always hide program stderr streams. `"nzec"` to only show stderr streams when programs have non-zero exit codes. |
| `"ext"`           | string | `""`     | yes       | The file extension of a language. Best to always define in the language object.                                                                                                                |
| `"show_prologue"` | bool   | `true`   | no        | Whether the leading output lines that start "RunMany Result" are shown.                                                                                                                        |
| `"show_runs"`     | bool   | `true`   | no        | Whether the list of runs (the bulk of the output) is shown.                                                                                                                                    |
| `"show_time"`     | bool   | `false`  | yes       | Whether the execution time of each program is shown.                                                                                                                                           |
| `"show_command"`  | bool   | `false`  | yes       | Whether the command used to run each program is shown.                                                                                                                                         |
| `"show_code"`     | bool   | `false`  | yes       | Whether the source code of the program is shown.                                                                                                                                               |
| `"show_argv"`     | bool   | `true`   | yes       | Whether the argv for the program is shown (when present).                                                                                                                                      |
| `"show_stdin"`    | bool   | `true`   | yes       | Whether the stdin for the program is shown (when present).                                                                                                                                     |
| `"show_output"`   | bool   | `true`   | yes       | Whether the output for the program is shown.                                                                                                                                                   |
| `"show_errors"`   | bool   | `true`   | no        | Whether RunMany errors like `***\| RunMany Error: ... \|***` are sent to stderr or silenced.                                                                                                   |
| `"show_epilogue"` | bool   | `true`   | no        | Whether the trailing output lines that count successful runs are shown.                                                                                                                        |

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
