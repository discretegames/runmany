"""Tests RunMany errors triggered by the print_err function."""

import io
import pathlib
from typing import Dict, Any, Union
from contextlib import redirect_stderr, redirect_stdout
from runmany import runmany
from runmany.util import PathLike, JsonLike


def stderr_of_run(manyfile: Union[PathLike, str], settings: JsonLike = None, from_string: bool = True) -> str:
    with io.StringIO() as file, redirect_stderr(file):
        runmany(manyfile, settings, from_string=from_string)
        file.seek(0)
        return file.read()


def test_json_combine_error() -> None:
    expected = '''||| RunMany Error: Issue combining JSONs "string indices must be integers". \
Something may be the wrong type. Using default settings JSON. |||\n'''
    assert stderr_of_run('', {"languages": {"name": "C"}}) == expected


def test_invalid_line() -> None:
    def expected(spaces: str) -> str:
        return f'||| RunMany Error: Skipping invalid unindented line 2 "{spaces}Argv:". |||\n'
    assert stderr_of_run('Argv:\nArgv:', {}) == ''
    assert stderr_of_run('Argv:\n Argv:', {}) == expected(' ')
    assert stderr_of_run('Argv:\n  Argv:', {}) == expected('  ')
    assert stderr_of_run('Argv:\n   Argv:', {}) == expected('   ')
    assert stderr_of_run('Argv:\n\tArgv:', {}) == ''
    assert stderr_of_run('Argv:\n    Argv:', {}) == ''
    expected2 = '||| RunMany Error: Skipping invalid unindented line 3 "Python". |||\n'
    assert stderr_of_run('Settings:\n\nPython', {}) == expected2


def test_no_name() -> None:  # this test only works on Windows
    def expected(json: Dict[str, Any]) -> str:
        return f'||| RunMany Error: No "name" key found for {str(json)}. Skipping language. |||\n'
    no_name_json = {"languages": [{"command": ""}]}
    assert stderr_of_run('', no_name_json) == expected(no_name_json['languages'][0])
    no_name_json = {"languages_windows": [{" name ": "C"}]}
    assert stderr_of_run('', no_name_json) == expected(no_name_json['languages_windows'][0])
    no_name_json = {"supplied_languages": [{"command": ""}]}
    assert stderr_of_run('', no_name_json) == expected(no_name_json['supplied_languages'][0])
    no_name_json = {"supplied_languages_windows": [{"NAME": "C"}]}
    assert stderr_of_run('', no_name_json) == expected(no_name_json['supplied_languages_windows'][0])
    no_name_json = {"languages": [{"name": "C"}]}
    assert stderr_of_run('', no_name_json) == ''


def test_no_command() -> None:
    with io.StringIO() as file, redirect_stdout(file):
        runmany('MyLang: x', {"minimalist": True, "languages": [{"name": "MyLang"}]}, from_string=True)
        file.seek(0)
        string = file.read()
    assert string.startswith('1. MyLang\nNOCOMMAND')


def test_unknown_language() -> None:
    many_file = "\nC+, Python,\t:"
    expected = '''\
||| RunMany Error: Language "C+" on line 2 not found in settings JSON. Skipping language. |||
||| RunMany Error: Language "" on line 2 not found in settings JSON. Skipping language. |||\n'''
    assert stderr_of_run(many_file, {}) == expected


def test_lines_outside_section() -> None:
    def expected(line_number: int, line: str) -> str:
        return f'||| RunMany Error: Line {line_number} "{line}" is not part of a section. Skipping line. |||\n'
    assert stderr_of_run('Also:', {}) == expected(1, 'Also:')
    assert stderr_of_run('C', {}) == expected(1, 'C')
    assert stderr_of_run('!Also:', {}) == expected(1, '!Also:')
    assert stderr_of_run('START:\nAlso \t:', {}) == expected(2, 'Also \t:')
    assert stderr_of_run('\nSTART:\nstuff', {}) == expected(3, 'stuff')
    assert stderr_of_run('C: foo\nEnd.\nAlso: bar', {}) == expected(3, 'Also: bar')
    assert stderr_of_run('End.', {}) == expected(1, 'End.')
    assert stderr_of_run('C:\nEnd.\nEnd.', {}) == expected(3, 'End.')
    assert stderr_of_run('C:\nEnd.\n%%End.', {}) == ''


def test_json_file_not_exist() -> None:
    expected = "||| RunMany Error: JSON file issue " \
        "\"[Errno 2] No such file or directory: 'does_not_exist.json'\". Using default settings JSON. |||\n"
    assert stderr_of_run('', 'does_not_exist.json') == expected
    assert stderr_of_run('Settings:"does_not_exist.json"') == expected


def test_json_base_type() -> None:
    expected = '||| RunMany Error: JSON base type must be dict or string, not int. Using default settings JSON. |||\n'
    assert stderr_of_run('', pathlib.Path(__file__).with_name('not_dict.json')) == expected
    assert stderr_of_run('Settings:[]') == expected.replace('int', 'list')


def test_json_decode_error() -> None:
    expected = '||| RunMany Error: JSON file issue ' \
        '"Expecting value: line 2 column 1 (char 1)". Using default settings JSON. |||\n'
    assert stderr_of_run('',  pathlib.Path(__file__).with_name('bad_json.json')) == expected
    expected = '||| RunMany Error: Embedded JSON issue ' \
        '"Expecting value: line 3 column 2 (char 4)". Using default settings JSON. |||\n'
    assert stderr_of_run(pathlib.Path(__file__).with_name('bad_settings.many'), None, False) == expected
    assert stderr_of_run("START:\nSettings:\n\t}") == expected


# flake8: noqa
def test_no_unindented_comment_error() -> None:
    many_file = '''\
Python:
    print(1)
%% a
 %% b
  %% c
   %% d
    %% e
     %% f
 	%% g
  	%% h
  	%% i
    	%% j
    print(2)
'''
    assert stderr_of_run(many_file) == ''
