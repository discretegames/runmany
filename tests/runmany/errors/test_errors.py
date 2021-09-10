import io
import pathlib
from typing import Dict, Any, Union
from runmany import runmany
from runmany.util import PathLike, JsonLike
from contextlib import redirect_stderr


def stderr_of_run(many_file: Union[PathLike, str], settings_json: JsonLike = None, from_string: bool = True) -> str:
    with io.StringIO() as file, redirect_stderr(file):
        runmany(many_file, settings_json, from_string=from_string)
        file.seek(0)
        return file.read()


def test_invalid_header() -> None:
    expected = \
        '!!!| RunMany Error: Skipping line 1 " Argv:" as it is not a valid section header and not indented. |!!!\n'
    assert stderr_of_run(' Argv:', {}) == expected
    expected = \
        '!!!| RunMany Error: Skipping line 1 "Python" as it is not a valid section header and not indented. |!!!\n'
    assert stderr_of_run('Python', {}) == expected


def test_no_block_comment_match() -> None:
    expected = '!!!| RunMany Error: No block comment to finish. Skipping line 3. |!!!\n'
    assert stderr_of_run('/%\n%/\n%/', {}) == expected


def test_no_name() -> None:
    no_name_json = {"languages": [{"command": ""}]}
    expected = '!!!| RunMany Error: No "name" key found for json list item. Ignoring language. |!!!\n'
    assert stderr_of_run('', no_name_json) == expected


def test_no_command() -> None:
    no_command_json = {"languages": [{"name": "Name"}]}
    expected = '!!!| RunMany Error: No "command" key found for Name. Ignoring language. |!!!\n'
    assert stderr_of_run('', no_command_json) == expected


def test_unknown_language() -> None:
    many_file = "C+, Python,\t:"
    expected = '''\
!!!| RunMany Error: Language "C+" on line 1 not found in settings JSON. Skipping language. |!!!
!!!| RunMany Error: Language "" on line 1 not found in settings JSON. Skipping language. |!!!\n'''
    assert stderr_of_run(many_file, {}) == expected


def test_no_lead_section() -> None:
    expected = '!!!| RunMany Error: No lead section for Also on line 1. Skipping section. |!!!\n'
    assert stderr_of_run('Also:', {}) == expected
    assert stderr_of_run('Also \t:', {}) == expected
    assert stderr_of_run('\nAlso :: stuff', {}) == expected.replace('1', '2')
    assert stderr_of_run('!Also:', {}) == ''
    assert stderr_of_run('!Also  :', {}) == ''


def test_json_type_error() -> None:
    bad_type_json = {"spacing": 2+3j}
    expected1 = "!!!| RunMany Error: JSON issue - "\
        "Object of type 'complex' is not JSON serializable. Using default settings JSON. |!!!\n"
    expected2 = expected1.replace("'", '')  # Python 3.6 doesn't put quotes around 'complex'.
    assert stderr_of_run('', bad_type_json) in (expected1, expected2)


def test_json_value_error() -> None:
    circular_json: Dict[str, Any] = {}
    circular_json["spacing"] = circular_json
    expected = '!!!| RunMany Error: JSON issue - Circular reference detected. Using default settings JSON. |!!!\n'
    assert stderr_of_run('', circular_json) == expected


def test_json_io_error() -> None:
    expected = "!!!| RunMany Error: JSON issue - "\
        "[Errno 2] No such file or directory: 'does_not_exist.json'. Using default settings JSON. |!!!\n"
    assert stderr_of_run('', 'does_not_exist.json') == expected


def test_json_not_dict() -> None:
    expected = '!!!| RunMany Error: JSON issue - The JSON must be an object/dict. Using default settings JSON. |!!!\n'
    assert stderr_of_run('', pathlib.Path(__file__).with_name('not_dict.json')) == expected


def test_json_decode_error() -> None:
    expected = '!!!| RunMany Error: JSON issue - '\
        'Expecting value: line 1 column 1 (char 0). Using default settings JSON. |!!!\n'
    assert stderr_of_run(pathlib.Path(__file__).with_name('decode_error.many'), None, False) == expected
