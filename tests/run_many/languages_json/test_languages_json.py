import io
import pathlib
from typing import Dict, Any
from contextlib import redirect_stderr
from run_many import runmany_to_s


default_json = {
    "all_name": "All",
    "check_equal": False,
    "timeout": 10.0,
    "stderr": False,
    "show_prologue": False,
    "show_runs": False,
    "show_command": False,
    "show_code": False,
    "show_argv": False,
    "show_stdin": False,
    "show_output": False,
    "show_errors": False,
    "show_epilogue": False
}

default_input = '''\
the prologue
@@@| Python |@@@
the argv
$$$| Python |$$$
the stdin
~~~| Python |~~~
print("the output")'''


def path_to(filename: str) -> pathlib.Path:
    return pathlib.Path(__file__).with_name(filename)


def combine_jsons(languages_json: Dict[str, Any]) -> Dict[str, Any]:
    return {key: languages_json.get(key, default_json[key]) for key in default_json}


def verify_output(languages_json: Dict[str, Any], output_file: str, many_file_contents: str = default_input) -> None:
    with open(path_to(output_file)) as file:
        expected = file.read()
        actual = runmany_to_s(many_file_contents, combine_jsons(languages_json), from_string=True)
        assert actual.strip('\r\n') == expected.strip('\r\n')


def test_all_name() -> None:
    languages_json = {"all_name": " every language ", "show_runs": True, "show_output": True}
    many_file = '''\
$$$| Every Language |$$$
abc
~~~| Python |~~~
print(input())
~~~| Python 2 |~~~
print raw_input()'''
    verify_output(languages_json, 'all_name.txt', many_file)


def test_check_equal() -> None:
    languages_json = {"check_equal": True, "show_epilogue": True}
    verify_output(languages_json, 'check_equal.txt')


def test_languages() -> None:
    assert 0


def test_timeout() -> None:
    assert 0


def test_stderr() -> None:
    assert 0


def test_show_prologue() -> None:
    verify_output({"show_prologue": True}, "show_prologue.txt")


def test_show_runs() -> None:
    verify_output({"show_runs": True}, "show_runs.txt")


def test_show_command() -> None:
    languages_json = combine_jsons({"show_runs": True, "show_command": True})
    actual = runmany_to_s(default_input, languages_json, from_string=True)
    assert actual.startswith("1. Python > python")


def test_show_errors() -> None:
    many_file = '~~~|~~~'
    with io.StringIO() as file, redirect_stderr(file):
        runmany_to_s(many_file, combine_jsons({"show_errors": True}), from_string=True)
        file.seek(0)
        assert file.read()
    with io.StringIO() as file, redirect_stderr(file):
        runmany_to_s(many_file, combine_jsons({"show_errors": False}), from_string=True)
        file.seek(0)
        assert not file.read()


def test_show_code() -> None:
    verify_output({"show_runs": True, "show_code": True}, "show_code.txt")


def test_show_argv() -> None:
    verify_output({"show_runs": True, "show_argv": True}, "show_argv.txt")


def test_show_stdin() -> None:
    verify_output({"show_runs": True, "show_stdin": True}, "show_stdin.txt")


def test_show_output() -> None:
    verify_output({"show_runs": True, "show_output": True}, "show_output.txt")


def test_show_epilogue() -> None:
    verify_output({"show_epilogue": True}, "show_epilogue.txt")
