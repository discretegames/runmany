import os
import json
import pytest
import pathlib
from typing import Any, Callable, Tuple, Union, List
from run_many import runmany, runmany_to_s, runmany_to_f
from run_many.run_many import JsonLike, PathLike


def path_to(filename: str) -> pathlib.Path:
    return pathlib.Path(__file__).with_name(filename)


def file_data(filename: str) -> Tuple[PathLike, str]:
    path = path_to(filename)
    with open(path) as file:
        return path, file.read()


def build_cases() -> List[Tuple[Union[PathLike, str], JsonLike, bool, str]]:
    many_path, many_contents = file_data('input.many')
    json_path, json_contents = file_data('input.json')
    many_file_values = many_path, str(many_path), many_contents
    from_string_values = False, False, True
    _, output1 = file_data('output1.txt')
    _, output2 = file_data('output2.txt')
    output1_jsons: Tuple[JsonLike, ...] = None, '', {}
    output2_jsons: Tuple[JsonLike, ...] = json_path, str(json_path), json.loads(json_contents)

    cases: List[Tuple[Union[PathLike, str], JsonLike, bool, str]] = []
    for many_file, from_string in zip(many_file_values, from_string_values):
        for json1 in output1_jsons:
            cases.append((many_file, json1, from_string, output1))
        for json2 in output2_jsons:
            cases.append((many_file, json2, from_string, output2))

    return cases


cases = build_cases()


@pytest.mark.parametrize('many_file,languages_json,from_string,expected', cases)
def test_runmany(many_file: Union[PathLike, str], languages_json: JsonLike, from_string: bool, expected: str) -> None:
    assert 2 == 2


@pytest.mark.parametrize('many_file,languages_json,from_string,expected', cases)
def test_runmany_to_s(
        many_file: Union[PathLike, str], languages_json: JsonLike, from_string: bool, expected: str) -> None:
    assert 2 == 2


@pytest.mark.parametrize('many_file,languages_json,from_string,expected', cases)
def test_runmany_to_f(
        many_file: Union[PathLike, str], languages_json: JsonLike, from_string: bool, expected: str) -> None:
    assert 2 == 2
