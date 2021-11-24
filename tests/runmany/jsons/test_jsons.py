# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring # TODO
import io
import json
import pathlib
from typing import Dict, Any, Optional, Callable
from contextlib import redirect_stderr
from runmany import runmanys

BASE_SETTINGS_JSON = {
    "languages": [],
    "timeout": 10.0,
    "stderr": True,
    "ext": "",
    "spacing": 1,
    "show_runs": False,
    "show_time": False,
    "show_command": False,
    "show_code": False,
    "show_argv": False,
    "show_stdin": False,
    "show_output": False,
    "show_errors": False,
    "show_stats": False,
    "show_equal": False
}

DEFAULT_MANY_FILE = '''\
Argv for Python: the argv
Stdin for Python: the stdin
Python: print("the output")
'''

# TODO
# minimalist
# newline
# tab
# 4x ignore
# 4x strip
# os language
# overwriting supplied?
# show time in footer


def path_to(filename: str) -> pathlib.Path:
    return pathlib.Path(__file__).with_name(filename)


def combine_with_base(settings_json: Dict[str, Any]) -> Dict[str, Any]:
    return {key: settings_json.get(key, val) for key, val in BASE_SETTINGS_JSON.items()}


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
        assert actual.splitlines()[1].startswith("1. Python (0.")
    settings_json = {"show_runs": True, "show_time": True}
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
