"""Tests all the RunMany syntax."""

import pathlib
from runmany import runmanys
# flake8: noqa

# TODO test these:
# - ! !! more
# - @ @@ soloed
# - End.
# - things outside of sections, including End. and at the start
# - START:
# - multiple settings
# - settings is path
# - %%% comments, especially after start/stop/sections, etc
# - line numbers for errors and such?

# Some testing code duplicated from test_jsons.py but ehh.
BASE_SETTINGS = {
    "timeout": 9.0,
    "extension": "",
    "command": "echo MISSINGCOMMAND",
    "spacing": 1,
    "minimalist": False,
    "stderr": "yes",
    "newline": "\n",
    "tab": "\t",

    "run_blanks": False,
    "run_comments": False,

    "strip_argv": "smart",
    "strip_stdin": "smart",
    "strip_code": "smart",
    "strip_output": "no",

    "show_runs": True,
    "show_stats": False,
    "show_equal": False,

    "show_errors": False,
    "show_time": False,
    "show_command": False,
    "show_code": False,
    "show_argv": True,
    "show_stdin": True,
    "show_output": True,

    "languages": [],
    "languages_windows": [],
    "languages_linux": [],
    "languages_mac": [],
}


def path_to(filename: str) -> pathlib.Path:
    return pathlib.Path(__file__).with_name(filename)


def verify(output_file: str, many_file: str) -> None:
    with open(path_to(output_file), encoding='utf-8') as file:
        expected = file.read()
        actual = runmanys(many_file, BASE_SETTINGS, from_string=True)
        assert actual.strip('\r\n') == expected.strip('\r\n')


def test_empty() -> None:
    verify('empty.txt', '')


def test_indents() -> None:
    many_file = '''\
Python: print(0)

 
  
   
    print(1)
\tprint(2)
'''
    verify('indents.txt', many_file)


def test_for_header() -> None:
    headers = '', ' for Python, Python 2', '\tfor  c,python 2 , python, \tjavascript  '
    for header in headers:
        many_file = f'''\
Stdin {header}: some input
Python: print(input())
Python 2: print raw_input()
'''
        verify('for_header.txt', many_file)


def test_all_header() -> None:
    many_file = '''\
Stdin:A
Also: B
Argv: 1
Also:2
Python:
    import sys
    print(input(), sys.argv[1])
Python 2:
    import sys
    print raw_input(), sys.argv[1]

Stdin for Python: X
Argv for Python: Y
Python:
    import sys
    print(input(), sys.argv[1])
Python 2:
    import sys
    print raw_input(), sys.argv[1]

Stdin:C
Also:D
Argv: M
Also: N
'''
    verify('all_header.txt', many_file)


def test_header_syntax() -> None:
    many_file = '''\
Argv    :
     A
Also\t: B

Stdin  for  python  :  1

PYTHON : import sys
\tprint(input(), sys.argv[1])

ARGV:
Argv for    python 2     :
Stdin:
STDIN: hmm
Python\t , Python 2  :\tprint(9)
'''
    verify('header_syntax.txt', many_file)


def test_code_list() -> None:
    many_file = '''\
Python, Python 2, Python:
    print('A')
Also: print('B')
Also:
    print('C')
'''
    verify('code_list.txt', many_file)


def test_argv() -> None:
    many_file = '''\
Argv: \t\t A X
Also:\t
    B Y
Also:
    C Z
Python, PYTHON 2 :
    import sys
    print(sys.argv[1])
Argv for python 2:
    overwrite
Python, Python 2:
    import sys
    print(sys.argv[1])
Argv:
Python: print('argv reset')
'''
    verify('argv.txt', many_file)


def test_stdin() -> None:
    many_file = '''\
Stdin:1
    2
Also:
    3
    4
Also:
    5
    6

Python, Python 2: print(input())
Stdin for Python 2: 0

Python, Python 2: print(input())

Stdin for Python:


Python: print('stdin reset')
'''
    verify('stdin.txt', many_file)


def test_disabled_sections() -> None:
    many_file = '''\
Stdin for Python:
    A
!!Stdin for Python:
    B
Python:
    print(1, input())
!Also: print(2, input())
Also:
    print(3, input())
!\t Also: print(4, input())
!!JavaScript:
    console.log('unseen 1')
Also:
    console.log('unseen 2')
! Python: print('unseen 3')
'''
    verify('disabled_sections.txt', many_file)


def test_leading_comments() -> None:
    many_file = '''\
% comment
Stdin: % 1
% 2
    % 3
% 4
    % 5
% 6
Python:
%Python:
%% comment
%STOP.
    print(input())
    input()
%
    print(input())
    input()
% % %
    x = 5%1; print(input())
'''
    verify('leading_comments.txt', many_file)


def test_stop() -> None:
    many_file = '''\
Python:
    print(1)
%STOP.
STOP..
 STOP.
Python:print(2)
STOP.
Python:print(3)
'''
    verify('stop.txt', many_file)


def test_similar() -> None:
    many_file = '''\
Stdin for Python:
    Python:
    Also:
    Argv for:
% Python:
Python:
    print(input())
    print(input())
    print(input())
'''
    verify('similar.txt', many_file)


def test_hardcoded_json() -> None:
    many_file = '''\
Settings: { "show_stats": false, "show_equal": false }
Python: print('x')
'''
    with open(path_to('hardcoded1.txt'), encoding='utf-8') as file:
        actual = runmanys(many_file, from_string=True)
        assert actual.strip('\r\n') == file.read().strip('\r\n')

    with open(path_to('hardcoded2.txt'), encoding='utf-8') as file:
        actual = runmanys(many_file, {}, from_string=True)
        assert actual.strip('\r\n') == file.read().strip('\r\n')
