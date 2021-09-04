import pathlib
from typing import Dict, Any
from run_many import runmany_to_s


# Some testing code duplicated from test_jsons.py but ehh.
base_settings_json = {
    "all_name": "All",
    "languages": [],
    "timeout": 10.0,
    "stderr": None,
    "ext": "",
    "spacing": 1,
    "show_runs": True,
    "show_time": False,
    "show_command": False,
    "show_code": False,
    "show_argv": True,
    "show_stdin": True,
    "show_output": True,
    "show_errors": False,
    "show_stats": False,
    "show_equal": False
}


def path_to(filename: str) -> pathlib.Path:
    return pathlib.Path(__file__).with_name(filename)


def verify(output_file: str, many_file: str) -> None:
    with open(path_to(output_file)) as file:
        expected = file.read()
        actual = runmany_to_s(many_file, base_settings_json, from_string=True)
        assert actual.strip('\r\n') == expected.strip('\r\n')


def test_empty() -> None:
    verify('empty.txt', '')


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
        verify('section_header.txt', many_file)


def test_code_list() -> None:
    many_file = '''\
~~~| Python | Python 2 | Python |~~~
print('A')
~~~|~~~
print('B')
~~~|~~~
print('C')
'''
    verify('code_list.txt', many_file)


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
    verify('argv.txt', many_file)


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
    verify('stdin.txt', many_file)


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
    verify('disabled_sections.txt', many_file)


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
    verify('comments.txt', many_file)


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
    verify('exit.txt', many_file)


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
    verify('similar.txt', many_file)


def test_hardcoded_json() -> None:
    many_file = '''\
{ "show_stats": false, "show_equal": false }
~~~| Python |~~~
print('x')
'''
    with open(path_to('hardcoded1.txt')) as file:
        actual = runmany_to_s(many_file, from_string=True)
        assert actual.strip('\r\n') == file.read().strip('\r\n')

    with open(path_to('hardcoded2.txt')) as file:
        actual = runmany_to_s(many_file, {}, from_string=True)
        assert actual.strip('\r\n') == file.read().strip('\r\n')
