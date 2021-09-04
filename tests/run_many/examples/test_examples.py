import pathlib
import pytest
from run_many import runmany_to_s

examples = []
for path in pathlib.Path('examples').iterdir():
    if path.is_file() and path.suffix == '.many' and path.stem != 'primes':
        examples.append(path)


@pytest.mark.slow
@pytest.mark.parametrize('path', examples)
def test_example(path: pathlib.Path) -> None:
    with open(path.with_name(f'{path.stem}_output.txt')) as output:
        assert runmany_to_s(path) == output.read()
