import pytest
from run_many import runmany_to_s

# TODO fix example output line, and in readme


def verify_example(filestem: str) -> None:
    file = f'examples/{filestem}.many'
    with open(f'examples/{filestem}_output.txt') as output:
        expected = output.read()
    actual = runmany_to_s(file)
    assert actual == expected


@pytest.mark.slow
def test_examples() -> None:
    examples = 'argv inputs helloworld polyglot'
    for filestem in examples.split():
        verify_example(filestem)
