import pathlib
from typing import Dict, Any
from run_many import runmany_to_s

# TODO test spacing

# Some testing code duplicated from test_jsons.py but ehh.
default_settings_json = {
    "all_name": "All",
    "check_equal": False,
    "languages": [],
    "timeout": 10.0,
    "stderr": None,
    "show_prologue": False,  # TODO change prologue test
    "show_runs": True,
    "show_command": False,
    "show_code": False,
    "show_argv": True,
    "show_stdin": True,
    "show_output": True,
    "show_errors": False,
    "show_epilogue": False
}


def path_to(filename: str) -> pathlib.Path:
    return pathlib.Path(__file__).with_name(filename)


def verify_output(output_file: str, many_file_contents: str) -> None:
    with open(path_to(output_file)) as file:
        expected = file.read()
        actual = runmany_to_s(many_file_contents, default_settings_json, from_string=True)
        assert actual.strip('\r\n') == expected.strip('\r\n')


def test_section_header() -> None:
    headers = 'All', 'Python | Python 2', 'c|python 2|python|javascript'
    for header in headers:
        many_file = f'''\
$$$| {header} |$$$
some input
~~~| Python |~~~
print(input())
~~~| Python 2 |~~~
print raw_input()
'''
        verify_output('section_header.txt', many_file)


def test_code_list() -> None:
    many_file = '''\
~~~| Python | Python 2 | Python |~~~
print('A')
~~~|~~~
print('B')
~~~|~~~
print('C')
'''
    verify_output('code_list.txt', many_file)


def test_argv() -> None:
    many_file = '''\
@@@| All |@@@
A X
@@@|@@@
B Y
@@@|@@@
C Z
~~~| Python | Python 2 |~~~
import sys
print(sys.argv[1])
@@@| Python 2 |@@@
overwrite
~~~| Python | Python 2 |~~~
import sys
print(sys.argv[1])

@@@| All |@@@
~~~| Python |~~~
print('argv reset')
'''
    verify_output('argv.txt', many_file)


def test_stdin() -> None:
    many_file = '''\
$$$| All |$$$
1
2
$$$|$$$
3
4
$$$|$$$
5
6
~~~| Python | Python 2 |~~~
print(input())
$$$| Python 2 |$$$
0
~~~| Python | Python 2 |~~~
print(input())

$$$| Python |$$$


~~~| Python |~~~
print('stdin reset')
'''
    verify_output('stdin.txt', many_file)


def test_disabled_sections() -> None:
    many_file = '''\
$$$| Python |$$$
A
!$$$| Python |$$$
B
~~~| Python |~~~
print(1, input())
!~~~|~~~
print(2, input())
~~~|~~~
print(3, input())
!~~~| JavaScript |~~~
console.log('unseen')
~~~|~~~
print(4, input())
'''
    verify_output('disabled_sections.txt', many_file)


def test_comments() -> None:
    many_file = '''\
%%%| comment |%%%
$$$| All |$$$
%%% |%%%
%%%||||%%%
 %%%||%%%
%%%||%%%
%%%| spacing matters |%%%
~~~| Python |~~~
!%%%| exclamation is ok |%%% 
!%%%|%%%
print(input())
%%%||%%%
print(input())
%%%| contents | don't |%%%
'''
    verify_output('comments.txt', many_file)


def test_exit() -> None:
    many_file = '''\
~~~| Python |~~~
print(1)
!%%%|%%%
~~~| Python |~~~
print(2)
%%%|%%%
~~~| Python |~~~
print(3)
'''
    verify_output('exit.txt', many_file)


def test_similar() -> None:
    many_file = '''\
$$$| Python |$$$
$$$|$$
 ~~~| Python |~~~
@@@|@@@!
~~~| Python |~~~	  
print(input())
print(input())
print(input())    
'''
    verify_output('similar.txt', many_file)


# TODO not here, but test totally empty file
'''
************************************************************
0/0 programs successfully run!
0/0 had the exact same stdout!
************************************************************
'''
