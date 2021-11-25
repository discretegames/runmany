# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring # TODO
import io
import json
import pathlib
from itertools import chain
from typing import Dict, Any, Optional, Callable
from contextlib import redirect_stderr
from runmany import runmanys

BASE_SETTINGS = {
    "timeout": 10.0,
    "extension": "",
    "command": "echo MISSINGCOMMAND",
    "spacing": 1,
    "minimalist": False,
    "stderr": "smart",
    "newline": "\n",
    "tab": "\t",

    "ignore_blank": True,
    "ignore_comment": False,
    "ignore_solo": False,
    "ignore_disable": False,

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

# TODO
# 4x ignore
# 4x strip


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


def test_ignore_blank() -> None:
    many_file = '''Python:'''
    settings_json = {"show_runs": True, "show_output": True}
    verify(settings_json, "ignore_blank1.txt", many_file)
    settings_json["ignore_blank"] = False
    verify(settings_json, "ignore_blank2.txt", many_file)


def test_ignore_comment() -> None:
    many_file = '''
Python: print("""foo%%%bar
    """.strip())
    print("""goo%%%far
    """.strip())'''
    settings_json = {"show_runs": True, "show_output": True, "show_code": True}
    verify(settings_json, "ignore_comment1.txt", many_file)
    settings_json["ignore_comment"] = True
    verify(settings_json, "ignore_comment2.txt", many_file)


# def test_ignore_solo() -> None:
#     many_file = '''\
# Python: print(0)
# @@Python: print(1)
# Also: print(2)
# @@@Python: print(3)
# Also: print(4)
# @@Python: print(5)
# @Also: print(6)
# @Python: print(7)
# Also: print(8)
# '''
#     settings_json = {"show_runs": True, "show_output": True, "minimalist": True}
#     verify(settings_json, "ignore_solo1.txt", many_file)


# def test_ignore_disable() -> None:
#     many_file = '''\
# !!Python: print(1)
# Also: print(2)
# Python: print(3)
# !Also: print(4)
# Also: print(5)
# !Python: print(6)
# Also: print(7)
# Python: print(8)
# '''
#     settings_json = {"show_runs": True, "show_output": True, "minimalist": True}
#     verify(settings_json, "ignore_disable1.txt", many_file)
#     settings_json["ignore_disable"] = True
#     verify(settings_json, "ignore_disable2.txt", many_file)


# TODO change keys

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
    settings["languages"] = [{"name": "Python", "command": "echo $unseen"}]
    # Still supplied2.txt below because languages is not combined with supplied_languages_windows.
    verify(settings, 'supplied2.txt', many_file)
    settings["languages_windows"] = [{"name": "Python", "command": "echo $3"}]
    verify(settings, 'supplied3.txt', many_file)


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
