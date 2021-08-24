# type: ignore
import io
import os
import json
from sys import path
import pytest
import pathlib
from contextlib import redirect_stdout


def path_to(filename):
    return pathlib.Path(__file__).with_name(filename)


def file_data(filename):
    path = path_to(filename)
    with open(path) as file:
        return path, file.read()


def build_cases():
    many_path, many_contents = file_data('input.many')
    json_path, json_contents = file_data('input.json')
    many_file_values = many_path, str(many_path), many_contents
    from_string_values = False, False, True
    _, output1 = file_data('output1.txt')
    _, output2 = file_data('output2.txt')
    output1_jsons = None, {}
    output2_jsons = json_path, str(json_path), json.loads(json_contents)

    cases = []
    for many_file, from_string in zip(many_file_values, from_string_values):
        for json1 in output1_jsons:
            cases.append((many_file, json1, from_string, output1))
        for json2 in output2_jsons:
            cases.append((many_file, json2, from_string, output2))

    return cases


def parametrize():
    return pytest.mark.parametrize('many_file,languages_json,from_string,expected', build_cases())


@parametrize()
def test_runmany(many_file, languages_json, from_string, expected):
    from run_many import runmany

    # Test outputting to stdout.
    with io.StringIO() as file, redirect_stdout(file):
        runmany(many_file, languages_json, from_string=from_string)
        file.seek(0)
        assert file.read() == expected

    # Test outputting to file:
    def verify_output_file(output_path):
        runmany(many_file, languages_json, output_path, from_string=from_string)
        with open(output_path) as f:
            assert f.read() == expected
        os.remove(output_path)

    output_path = path_to('test_output')
    verify_output_file(output_path)
    verify_output_file(str(output_path))


@parametrize()
def test_runmany_to_s(many_file, languages_json, from_string, expected):
    from run_many import runmany_to_s
    assert runmany_to_s(many_file, languages_json, from_string=from_string) == expected


@parametrize()
def test_runmany_to_f(many_file, languages_json, from_string, expected):
    from run_many import runmany_to_f
    with io.StringIO() as file:
        runmany_to_f(file, many_file, languages_json, from_string=from_string)
        file.seek(0)
        assert file.read() == expected


def test_cmdline():
    from run_many import cmdline
    many_path = str(path_to('input.many'))
    json_path = str(path_to('input.json'))
    _, output1 = file_data('output1.txt')
    _, output2 = file_data('output2.txt')

    def verify_to_stdout(argv, output):
        with io.StringIO() as file, redirect_stdout(file):
            cmdline(argv)
            file.seek(0)
            assert file.read() == output

    verify_to_stdout([many_path], output1)
    verify_to_stdout([many_path, '-j', json_path], output2)
    verify_to_stdout([many_path, '--json', json_path], output2)
    verify_to_stdout(['-j', json_path, many_path], output2)

    output_path = str(path_to('test_output'))

    def verify_to_file(argv, output):
        cmdline(argv)
        with open(output_path) as f:
            assert f.read() == output
        os.remove(output_path)

    verify_to_file([many_path, '-o', output_path], output1)
    verify_to_file([many_path, '--output', output_path], output1)
    verify_to_file([many_path, '-j', json_path, '-o', output_path], output2)
    verify_to_file([many_path, '-j', json_path, '--output', output_path], output2)
    verify_to_file(['-o', output_path, '-j', json_path, many_path], output2)
