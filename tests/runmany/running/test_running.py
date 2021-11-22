
# type: ignore
import io
import os
import json
import pathlib
from contextlib import redirect_stdout
import pytest


def path_to(filename):
    return pathlib.Path(__file__).with_name(filename)


def file_data(filename):
    path = path_to(filename)
    with open(path, encoding='utf-8') as file:
        return path, file.read()


def build_cases():  # pylint: disable=too-many-locals
    many_path, many_contents = file_data('input.many')
    json_path, json_contents = file_data('input.json')
    many_file_values = many_path, str(many_path), many_contents
    from_string_values = False, False, True
    _, output1 = file_data('output1.txt')
    _, output2 = file_data('output2.txt')
    output1_jsons = None, {"show_equal": False}
    output2_jsons = json_path, str(json_path), json.loads(json_contents)

    cases = []
    for many_file, from_string in zip(many_file_values, from_string_values):
        for json1 in output1_jsons:
            cases.append((many_file, json1, from_string, output1))
        for json2 in output2_jsons:
            cases.append((many_file, json2, from_string, output2))

    return cases


# pylint: disable=no-member
def parametrize():
    return pytest.mark.parametrize('many_file,settings_json,from_string,expected', build_cases())


@pytest.mark.slow
@parametrize()
def test_runmany(many_file, settings_json, from_string, expected):
    from runmany import runmany  # pylint: disable=import-outside-toplevel

    # Test outputting to stdout.
    with io.StringIO() as file, redirect_stdout(file):
        runmany(many_file, settings_json, from_string=from_string)
        file.seek(0)
        assert file.read() == expected

    # Test outputting to file:
    def verify_output_file(output_path):
        runmany(many_file, settings_json, output_path, from_string=from_string)
        with open(output_path, encoding='utf-8') as file:
            assert file.read() == expected
        os.remove(output_path)

    output_path = path_to('test_output')
    verify_output_file(output_path)
    verify_output_file(str(output_path))


@parametrize()
def test_runmanys(many_file, settings_json, from_string, expected):
    from runmany import runmanys  # pylint: disable=import-outside-toplevel
    assert runmanys(many_file, settings_json, from_string=from_string) == expected

# TODO redo test
# @parametrize()
# def test_runmany_to_f(many_file, settings_json, from_string, expected):
#     from runmany import runmany_to_f  # pylint: disable=import-outside-toplevel
#     with io.StringIO() as file:
#         runmany_to_f(file, many_file, settings_json, from_string=from_string)
#         file.seek(0)
#         assert file.read() == expected


def test_cmdline():
    from runmany import cmdline  # pylint: disable=import-outside-toplevel
    manyfile = str(path_to('input.many'))
    settings = str(path_to('input.json'))
    _, output1 = file_data('output1.txt')
    _, output2 = file_data('output2.txt')

    def verify_to_stdout(argv, output):
        with io.StringIO() as file, redirect_stdout(file):
            cmdline(argv)
            file.seek(0)
            assert file.read() == output

    verify_to_stdout([manyfile], output1)
    verify_to_stdout([manyfile, '-s', settings], output2)
    verify_to_stdout([manyfile, '--settings', settings], output2)
    verify_to_stdout(['-s', settings, manyfile], output2)

    outfile = str(path_to('test_output'))

    def verify_to_file(argv, output):
        cmdline(argv)
        with open(outfile, encoding='utf-8') as file:
            assert file.read() == output
        os.remove(outfile)

    verify_to_file([manyfile, '-o', outfile], output1)
    verify_to_file([manyfile, '--outfile', outfile], output1)
    verify_to_file([manyfile, '-s', settings, '-o', outfile], output2)
    verify_to_file([manyfile, '-s', settings, '--outfile', outfile], output2)
    verify_to_file(['-o', outfile, '-s', settings, manyfile], output2)
