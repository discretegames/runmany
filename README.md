# RunMany

A way to run many programming languages in one file.

Readme is just a todo list for now.

## TODO

Soon:

- Better formatting of output.
- Option for showing stderr and more info or not.
  - stderr
  - command
  - return code
- Put errors into section stdout when possible. (Strict/silent mode option?)
- Better, more descriptive error text in general for:
  - No lang name found (no natural output)
  - No lang command found (no natural output)
  - $ext missing (no natural output)
  - Language in header not found (no natural output exactly)
  - Timed out
  - Missing lead section (no natural output)
  - No matching lead section (no natural output)
  - special error line like !!!| RunMany error: Missing language |!!!
  
- Option to check for stdout equality. Display success at the end and differing ones.
- Turn into a pip package. "pip install runmany" then "runmany example.many".
- Block comment or "exit here" construct e.g. |||!|||
- Command line runnable with input+output+json file options. (Maybe inner json options too?)

Less Soon:

- Docstrings.
- Automated testing.
- A vscode plugin for syntax highlighting and running .many files??
