import io
from typing import Dict, Any
from run_many import runmany
from contextlib import redirect_stderr


def stderr_of_run(many_file_contents: str, languages_json_dict: Dict[str, Any]) -> str:
    with io.StringIO() as file, redirect_stderr(file):
        runmany(many_file_contents, languages_json_dict, from_string=True)
        file.seek(0)
        return file.read()


def test_no_name() -> None:
    no_name_json = {"languages": [{"command": ""}]}
    expected = '***| Run Many Error: No "name" key found for json list item. Ignoring language. |***\n'
    assert stderr_of_run('', no_name_json) == expected


def test_name_matches_all() -> None:
    all_match_json = {"languages": [{"name": " all ", "command": ""}]}
    expected = '***| Run Many Error: Language name " all " cannot match all_name "All". Ignoring language. |***\n'
    assert stderr_of_run('', all_match_json) == expected

    new_all_json = {"all_name": " every ", "languages": [{"name": " all ", "command": ""}]}
    assert stderr_of_run('', new_all_json) == ''

    new_all_match_json = {"all_name": " every ", "languages": [{"name": "EVERY", "command": ""}]}
    expected = '***| Run Many Error: Language name "EVERY" cannot match all_name " every ". Ignoring language. |***\n'
    assert stderr_of_run('', new_all_match_json) == expected


def test_no_command() -> None:
    no_command_json = {"languages": [{"name": "Name"}]}
    expected = '***| Run Many Error: No "command" key found for Name. Ignoring language. |***\n'
    assert stderr_of_run('', no_command_json) == expected


def test_unknown_language() -> None:
    many_file = "~~~| C+ | Python | \t |~~~"
    expected = '''\
***| Run Many Error: Language "C+" in section header at line 1 not found in json. Skipping language. |***\n\
***| Run Many Error: Language "" in section header at line 1 not found in json. Skipping language. |***\n'''
    assert stderr_of_run(many_file, {}) == expected


def test_no_lead_section() -> None:
    def expected_error(divider: str, line: int = 1) -> str:
        return f'***| Run Many Error: No matching lead section for "{divider}" on line {line}. Skipping section. |***\n'

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
