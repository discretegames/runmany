"""Verifies .many files in /examples folder work."""

from run_many import runmany_to_s


def verify_example(filestem: str) -> None:
    file = f'examples/{filestem}.many'
    with open(f'examples/{filestem}_output.txt') as output:
        expected = output.read()
    actual = runmany_to_s(file)
    assert actual == expected


def test_examples() -> None:
    examples = 'argv hellolanguage helloworld polyglot sample'
    for filestem in examples.split():
        verify_example(filestem)
