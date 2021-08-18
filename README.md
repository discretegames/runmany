# RunMany

A way to run many programming languages in one file.

Readme is just a todo list for now.

## TODO

Soon:

- Add $argv to json commands and test
- Better formatting of output.
  - consider stdin and argv
  - Show info of successful runs at bottom. The number of errors vs successes.
    - e.g. "46/60 programs run successfully. 14 had timeout errors or non zero exit codes."
- Option for showing stderr and more info or not.
  - stderr
  - command
  - return code
- Put errors into section stdout when possible. (Strict/silent mode option?)
- Timed out msg and exit code
- Option to check for stdout equality. Display success at the end and differing ones.
- Command line runnable with input+output+json file options. (Maybe inner json options too?)
- Turn into a pip package. "pip install runmany" then "runmany example.many".
  - Make sure correct path to language.json is used in pip version.
- Just ignore commented sections. More efficient.

Less Soon:

- Docstrings.
- Automated testing.
- A vscode plugin for syntax highlighting and running .many files??
