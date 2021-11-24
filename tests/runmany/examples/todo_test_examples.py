# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring # TODO
import pathlib
from typing import List
import pytest
from runmany import runmanys


def get_examples() -> List[pathlib.Path]:
    examples = []
    for path in pathlib.Path('examples').iterdir():
        if path.is_file() and path.suffix == '.many' and path.stem != 'primes':
            examples.append(path)
    return examples


# pylint: disable=no-member
@pytest.mark.slow
@pytest.mark.parametrize('path', get_examples())
def test_example(path: pathlib.Path) -> None:
    with open(path.with_name(f'{path.stem}_output.txt'), encoding='utf-8') as output:
        assert runmanys(path) == output.read()
