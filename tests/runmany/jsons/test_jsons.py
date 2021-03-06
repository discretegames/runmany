"""Tests all the JSON settings."""

import io
import json
import pathlib
from itertools import chain
from typing import Dict, Any, Optional, Callable, List
from contextlib import redirect_stderr
from runmany import runmanys

BASE_SETTINGS = {
    "timeout": 10.0,
    "extension": "",
    "command": "echo NOCOMMAND",
    "spacing": 1,
    "minimalist": False,
    "stderr": "smart",
    "newline": "\n",
    "tab": "\t",
    "run_blanks": False,
    "cwd": None,

    "strip_argv": "smart",
    "strip_stdin": "smart",
    "strip_code": "smart",
    "strip_output": "no",

    "show_runs": False,
    "show_stats": False,
    "show_equal": False,

    "show_errors": False,
    "show_time": False,
    "show_command": False,
    "show_code": False,
    "show_argv": False,
    "show_stdin": False,
    "show_output": False,

    "languages": [],
    "languages_windows": [],
    "languages_linux": [],
    "languages_mac": [],
}

DEFAULT_MANY_FILE = '''\
Argv for Python: the argv
Stdin for Python: the stdin
Python: print("the output")
'''

SMARTS: List[Any] = ['smart', None, ' Smart ', '', 'foo']
YESES: List[Any] = ['yes', True, ' Yes ']
NOS: List[Any] = ['no', False, ' No ']


def path_to(filename: str) -> pathlib.Path:
    return pathlib.Path(__file__).with_name(filename)


def combine_with_base(settings_json: Dict[str, Any]) -> Dict[str, Any]:
    return {key: settings_json.get(key, BASE_SETTINGS.get(key)) for key in chain(BASE_SETTINGS, settings_json)}


def default_asserter(actual: str, expected: str) -> None:
    assert actual.strip('\r\n') == expected.strip('\r\n')


def verify(settings_json: Dict[str, Any], output_file: Optional[str] = None, many_file: str = DEFAULT_MANY_FILE,
           asserter: Callable[[str, str], None] = default_asserter) -> None:
    if output_file is None:
        expected = ''
    else:
        with open(path_to(output_file), encoding='utf-8') as file:
            expected = file.read()

    settings_json = combine_with_base(settings_json)
    settings_json_string = json.dumps(settings_json)

    hardcoded_json_result = runmanys(f'Settings: {settings_json_string}\n{many_file}', from_string=True)
    asserter(hardcoded_json_result, expected)

    provided_json_result = runmanys(f'\n{many_file}', settings_json, from_string=True)
    asserter(provided_json_result, expected)


def test_cwd() -> None:
    many_file = '''\
Python, Python 2:
    try:
        FileNotFoundError
    except NameError:
        FileNotFoundError = IOError
    try:
        with open('cwd_helper.txt', 'r') as f:
                print(f.read())
    except FileNotFoundError:
        print('not found')
'''
    settings_json = {"cwd": "./tests/runmany/jsons", "show_runs": True, "show_output": True}
    verify(settings_json, 'cwd1.txt', many_file)
    settings_json = {"languages": [{"name": "Python", "cwd": "./tests/runmany/jsons"}],
                     "show_runs": True, "show_output": True}
    verify(settings_json, 'cwd2.txt', many_file)


def test_runs() -> None:
    many_file = '''\
Python: print(3)
Python 2: print 2
'''
    settings_json: Dict[str, Any] = {"runs": 0, "show_runs": True, "show_output": True}
    verify(settings_json, 'runs.txt', many_file)

    def asserter(actual: str, _: str) -> None:
        assert actual.endswith(" total)\n3\n\n\n2. Python 2\n2\n\n\n")
        assert "11" in actual

    settings_json = {"show_runs": True, "show_output": True, "minimalist": True,
                     "languages": [{"name": "Python", "show_time": True, "runs": 11}]}
    verify(settings_json, None, many_file, asserter)


def test_run_blanks() -> None:
    many_file = '''Python:'''
    settings_json = {"show_runs": True, "show_output": True}
    verify(settings_json, "run_blanks1.txt", many_file)
    settings_json["run_blanks"] = True
    verify(settings_json, "run_blanks2.txt", many_file)

    many_file = '''\
Argv:
Stdin:
Python: import sys
    print(sys.argv[1:])
    print(repr(sys.stdin.read()))
'''
    settings_json = {"show_runs": True, "show_output": True, "strip_argv": True, "show_argv": True, "show_stdin": True}
    verify(settings_json, "run_blanks3.txt", many_file)
    settings_json["run_blanks"] = True
    verify(settings_json, "run_blanks4.txt", many_file)


def test_strip_argv() -> None:
    many_file = '''\
Argv:
    a b		c
    d
End.
Python: import sys
    print(sys.argv[1:])
'''
    settings_json: Dict[str, Any] = {"show_runs": True, "show_output": True, "minimalist": True}
    for val in SMARTS:
        settings_json["strip_argv"] = val
        verify(settings_json, 'strip_argv_smart.txt', many_file)
    for val in YESES:
        settings_json["strip_argv"] = val
        verify(settings_json, 'strip_argv_yes.txt', many_file)
    for val in NOS:
        settings_json["strip_argv"] = val
        verify(settings_json, 'strip_argv_no.txt', many_file)


def test_strip_stdin() -> None:
    many_file = '''\
Stdin:
    AA
    BB



End.
Python: import sys
    with sys.stdin as f:
        print(repr(f.read()))
'''
    settings_json: Dict[str, Any] = {"show_runs": True, "show_output": True, "minimalist": True}
    for val in SMARTS:
        settings_json["strip_stdin"] = val
        verify(settings_json, 'strip_stdin_smart.txt', many_file)
    for val in YESES:
        settings_json["strip_stdin"] = val
        verify(settings_json, 'strip_stdin_yes.txt', many_file)
    for val in NOS:
        settings_json["strip_stdin"] = val
        verify(settings_json, 'strip_stdin_no.txt', many_file)


def test_strip_code() -> None:
    many_file = '''\
!Python:
End.
Python:


    pass

    raise Exception
'''

    def make_asserter(line: int) -> Callable[[str, str], None]:
        def asserter(actual: str, _: str) -> None:
            assert f'line {line}' in actual
        return asserter

    settings_json: Dict[str, Any] = {"show_code": True, "show_runs": True, "show_output": True, "minimalist": True}
    for val in SMARTS:
        settings_json["strip_code"] = val
        verify(settings_json, None, many_file, make_asserter(9))
    for val in YESES:
        settings_json["strip_code"] = val
        verify(settings_json, None, many_file, make_asserter(3))
    for val in NOS:
        settings_json["strip_code"] = val
        verify(settings_json, None, many_file, make_asserter(6))


def test_strip_output() -> None:
    many_file = '''Python: print('\\n\\n foo \\t\\n\\n')'''
    settings_json: Dict[str, Any] = {"show_runs": True, "show_output": True, "minimalist": True}
    for val in SMARTS:
        settings_json["strip_output"] = val
        verify(settings_json, 'strip_output_smart.txt', many_file)
    for val in YESES:
        settings_json["strip_output"] = val
        verify(settings_json, 'strip_output_yes.txt', many_file)
    for val in NOS:
        settings_json["strip_output"] = val
        verify(settings_json, 'strip_output_no.txt', many_file)


def test_minimalist() -> None:
    many_file = '''\
Python: print("hi")
JavaScript: console.log("hi")
'''
    settings_json = {"minimalist": True, "show_runs": True, "show_output": True, "show_stats": True}
    verify(settings_json, 'minimalist1.txt', many_file)
    settings_json["show_stats"] = False
    verify(settings_json, 'minimalist2.txt', '')


def test_newline() -> None:
    many_file = '''\
Python: print("a
    b
    c
    d")
End.
'''
    settings_json = {"show_runs": True, "show_output": True, "newline": "+", "strip_code": "yes"}
    verify(settings_json, 'newline.txt', many_file)


def test_tab() -> None:
    many_file = '''\
Python:
    for i in range(1, 4):
        print(i)
    \tprint(2 * i)
'''
    settings_json = {"show_runs": True, "show_output": True, "tab": "    "}
    verify(settings_json, 'tab.txt', many_file)


def test_languages() -> None:
    many_file = '''\
Python: print(3)
Python 2: print 2
'''
    settings_json = {"show_runs": True, "languages": [{"name": "Python", "show_code": True}]}
    verify(settings_json, 'languages1.txt', many_file)
    settings_json = {"show_runs": True, "show_output": True,
                     "languages": [{"name": "Python", "command": "echo $echoed"}]}
    verify(settings_json, 'languages2.txt', many_file)
    settings_json = {"show_runs": True, "show_output": True,
                     "languages": [{"name": "\tCUSTOM  language ", "command": "echo custom$thing"}]}
    verify(settings_json, 'languages3.txt', 'Custom Language:1\nCustom  Language:2')


def test_os_languages() -> None:
    many_file = '''Python: print('python')'''
    settings: Dict[str, Any] = {"show_runs": True, "show_output": True}
    verify(settings, 'os_languages1.txt', many_file)

    os_languages = [{"name": "Python", "command": "echo $os"}]
    settings["languages"] = [{"name": "Python", "command": "echo $default"}]
    verify(settings, 'os_languages2.txt', many_file)

    settings["languages_windows"] = os_languages
    settings["languages_linux"] = os_languages
    settings["languages_mac"] = os_languages
    verify(settings, 'os_languages3.txt', many_file)


def test_supplied_languages() -> None:  # Should only pass on Windows.
    many_file = '''Python: print('python')'''
    settings: Dict[str, Any] = {"show_runs": True, "show_output": True, "minimalist": True}
    settings["supplied_languages"] = [{"name": "Python", "command": "echo $1"}]
    verify(settings, 'supplied1.txt', many_file)
    settings["supplied_languages_windows"] = [{"name": "Python", "command": "echo $2"}]
    verify(settings, 'supplied2.txt', many_file)
    settings["languages"] = [{"name": "python", "command": "echo $3"}]
    verify(settings, 'supplied3.txt', many_file)
    settings["languages_windows"] = [{"name": "  pythoN  ", "command": "echo $4"}]
    verify(settings, 'supplied4.txt', many_file)  # also tests for full language arrays overwriting


def test_timeout() -> None:
    many_file = '''\
Python:
    import time
    time.sleep(0.1)
'''
    settings_json = {"show_runs": True, "show_output": True, "timeout": 0.09}
    verify(settings_json, 'timeout1.txt', many_file)
    settings_json = {"show_runs": True, "show_output": True, "timeout": 0.5}
    verify(settings_json, 'timeout2.txt', many_file)


def test_stderr() -> None:
    many_file = '''\
Python:
    import sys
    sys.stderr.write("to stderr\\n")
    print("to stdout")
    sys.exit(1)
'''
    for name, alt in ('yes', True), ('smart', None), ('no', False):
        for value in (name, alt):
            settings_json = {"show_runs": True, "show_output": True, "stderr": value}
            verify(settings_json, f'stderr_{name}.txt', many_file)


def test_spacing() -> None:
    many_file = '''\
Python: print("A")
Python: print("B")
'''
    settings_json = {"spacing": 0, "show_runs": True, "show_output": False, "show_code": True}
    verify(settings_json, 'spacing1.txt', many_file)
    settings_json = {"spacing": 5, "show_runs": True, "show_output": True}
    verify(settings_json, 'spacing2.txt', many_file)


def test_show_runs() -> None:
    many_file = '''\
Python,Python,Python:print("\\
\trun")
'''
    verify({"show_runs": True}, "show_runs1.txt", many_file)
    verify({"show_runs": False}, "show_runs2.txt", many_file)


def test_show_time() -> None:
    def asserter(actual: str, _: str) -> None:
        assert actual.splitlines()[1].startswith("1. Python (0.0")
        assert actual.splitlines()[4].startswith("1/1 program successfully run in 0.0")
    settings_json = {"show_runs": True, "show_time": True, "show_stats": True}
    verify(settings_json, None, DEFAULT_MANY_FILE, asserter)


def test_show_command() -> None:
    def asserter(actual: str, _: str) -> None:
        assert actual.splitlines()[1].startswith("1. Python > python")
    settings_json = {"show_runs": True, "show_command": True}
    verify(settings_json, None, DEFAULT_MANY_FILE, asserter)


def test_show_code() -> None:
    verify({"show_runs": True, "show_code": True}, "show_code.txt")


def test_show_argv() -> None:
    verify({"show_runs": True, "show_argv": True}, "show_argv.txt")


def test_show_stdin() -> None:
    verify({"show_runs": True, "show_stdin": True}, "show_stdin.txt")


def test_show_output() -> None:
    verify({"show_runs": True, "show_output": True}, "show_output.txt")


def test_show_errors() -> None:
    for many_file in 'Also:', 'Python', 'End.', '    End':
        with io.StringIO() as file, redirect_stderr(file):
            runmanys(many_file, combine_with_base({"show_errors": True}), from_string=True)
            file.seek(0)
            assert file.read()
        with io.StringIO() as file, redirect_stderr(file):
            runmanys(many_file, combine_with_base({"show_errors": False}), from_string=True)
            file.seek(0)
            assert not file.read()


def test_show_stats() -> None:
    verify({"show_stats": True}, "show_stats.txt")


def test_show_equal() -> None:
    many_file = '''\
Python, Python : print("A")
Python:\n    print("B")
'''
    verify({"show_equal": True}, "show_equal.txt", many_file)


def test_footer() -> None:
    many_file = '''\
Python: print(0)
Python:
    import sys
    print(1)
    sys.exit(1)
Python: print(0)
'''
    verify({"show_equal": True, "show_stats": True}, "footer.txt", many_file)
