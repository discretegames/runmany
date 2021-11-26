"""Tests all the RunMany syntax."""

import io
import pathlib
from contextlib import redirect_stderr
from runmany import runmanys
# flake8: noqa
# pylint: skip-file

# TODO test these:
# - ! !! more
# - @ @@ soloed

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

    "show_errors": True,
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


def verify(output_file: str, many_file: str, no_base_settings: bool = False) -> None:
    with open(path_to(output_file), encoding='utf-8') as file:
        expected = file.read()
        base_settings = None if no_base_settings else BASE_SETTINGS
        actual = runmanys(many_file, base_settings, from_string=True)
        assert actual.strip('\r\n') == expected.strip('\r\n')


def test_empty() -> None:
    verify('empty.txt', '')


def test_settings() -> None:
    many_file = '''\
Settings: {"languages_windows": [{"name": "Print", "newline": "N"}]}
Print: 1
	2

Settings:
Print: 3
	4

Settings: {"show_equal": false}
Print: 5
	6
'''
    verify('settings1.txt', many_file, True)
    verify('settings1b.txt', many_file, False)


def test_settings_path() -> None:
    many_file = '''\
Settings: ".\\\\tests\\\\runmany\\\\jsons\\\\settings_path.json"
Print: A
	B
	C
Settings: {
		"newline": "bar"
	}
Print: A
	B
	C
'''
    verify('settings2.txt', many_file, True)


def test_end() -> None:
    many_file = '''\
Argv: End.
    End.
End.
    End.
Stdin: End.
    End.
End.
    End.
Python:
    import sys
	print(sys.argv[1:])
    print(repr(input()))
End.
    print(123)
Python: 
    print(456)
End.
'''

    with io.StringIO() as stderr, redirect_stderr(stderr):
        verify('end.txt', many_file)
        stderr.seek(0)
        errors = stderr.read()
        assert '"    End." is not part of a section.' in errors
        assert '"    print(123)" is not part of a section' in errors


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


def test_disabled1() -> None:
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
    verify('disabled1.txt', many_file)


def test_disabled2() -> None:
    many_file = '''\
!Python: print(1)
Also: print(2)
!Also: print(3)
Also: print(4)

!!Python: print(5)
Also: print(6)

!!@Python: print(7)
Also: print(8)

Python: print(9)
!Also: print(10)
'''
    verify('disabled2.txt', many_file)


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


def test_inline_comments() -> None:
    many_file = '''\
Python: print('unseen2')
START: %%% ok1
	%%% ok2
Stdin: a %%% b
Argv: c %%% d
Python: import sys %%% i()
	print(sys.argv[1:]) %%% }
%%% j()
    %%% k()
	print(input()) %%% ]
End. %%% ok3
%%% ok4
	%%% ok5
STOP. %%% ok6
Python: print('unseen2')
'''
    with io.StringIO() as stderr, redirect_stderr(stderr):
        verify('inline_comments.txt', many_file)
        stderr.seek(0)
        assert stderr.read() == ''


def test_stop() -> None:
    many_file = '''\
Python:
    print(1)
%STOP.
stop:
STOP..
 STOP.
Python:print(2)
STOP.
Python:print(3)
'''
    verify('stop.txt', many_file)


def test_start() -> None:
    many_file = '''\
start:
Python: print(1)
Start:
Python: print(2)
% START:
Python: print(3)
START::
Python: print(4)
START: Python: print(5)
 START:
Python: print(6)
START :
Python: print(7)
START:
Python: print(8)
'''
    verify('start.txt', many_file)


def test_start_stop() -> None:
    many_file = '''\
Print: 1
START:
Print: 2
STOP.
Print: 3
'''
    verify('start_stop.txt', many_file)

    many_file = '''\
Print: 1
STOP.
Print: 2
START:
Print: 3

'''
    verify('empty.txt', many_file)


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
