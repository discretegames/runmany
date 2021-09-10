import io
import pathlib
from typing import Dict, Any, Union
from runmany import runmany
from runmany.util import PathLike, JsonLike
from contextlib import redirect_stderr

# todo test non matching block comment error
# todo test non-indented non-header


def stderr_of_run(many_file: Union[PathLike, str], settings_json: JsonLike = None, from_string: bool = True) -> str:
    with io.StringIO() as file, redirect_stderr(file):
        runmany(many_file, settings_json, from_string=from_string)
        file.seek(0)
        return file.read()


def test_no_name() -> None:
    no_name_json = {"languages": [{"command": ""}]}
    expected = '!!!| RunMany Error: No "name" key found for json list item. Ignoring language. |!!!\n'
    assert stderr_of_run('', no_name_json) == expected


def test_no_command() -> None:
    no_command_json = {"languages": [{"name": "Name"}]}
    expected = '!!!| RunMany Error: No "command" key found for Name. Ignoring language. |!!!\n'
    assert stderr_of_run('', no_command_json) == expected


# todo need to check for this style of error
def todo_test_unknown_language() -> None:
    many_file = "C+, Python,\t:"
    expected = '''\
!!!| RunMany Error: Language "C+" in section header at line 1 not found in json. Skipping language. |!!!\n\
!!!| RunMany Error: Language "" in section header at line 1 not found in json. Skipping language. |!!!\n'''
    assert stderr_of_run(many_file, {}) == expected

# todo need to rewrite this one


def todo_test_no_lead_section() -> None:
    def expected_error(divider: str, line: int = 1) -> str:
        return f'!!!| RunMany Error: No matching lead section for "{divider}" on line {line}. Skipping section. |!!!\n'

    def check_divider(divider: str) -> None:
        assert stderr_of_run(divider, {}) == expected_error(divider)

    check_divider('@@@|@@@')
    check_divider('$$$|$$$')
    check_divider('~~~|~~~')

    many_file = '~~~| Python |~~~\n@@@|@@@\n~~~|~~~'
    expected = expected_error('@@@|@@@', 2)
    assert stderr_of_run(many_file, {}) == expected

    many_file = '@@@| All |@@@\n$$$|$$$'
    expected = expected_error('$$$|$$$', 2)
    assert stderr_of_run(many_file, {}) == expected

    many_file = '$$$| all |$$$\n~~~|~~~'
    expected = expected_error('~~~|~~~', 2)
    assert stderr_of_run(many_file, {}) == expected

    assert stderr_of_run('!~~~|~~~', {}) == ''
    assert stderr_of_run('~~~| Python |~~~\n!$$$|$$$~~~|~~~', {}) == ''


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
