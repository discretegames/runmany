"""Package setup file for the Python 3 run-many package: https://pypi.org/project/run-many"""

from pathlib import Path
from setuptools import setup, find_packages

version = "0.1.1"

with open(Path(__file__).with_name('README.md'), encoding='utf-8') as file:
    long_description = file.read()

setup(
    name='run_many',
    version=version,
    author='discretegames',
    author_email='discretizedgames@gmail.com',
    description="A tool to run many programs written in many languages from one file.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/discretegames/runmany',
    packages=['run_many'],
    package_data={'run_many': ['default_languages.json']},
    license="MIT",
    keywords=['run', 'execute', 'other languages', 'multiple languages', 'manyfile',
              '.many', 'one file', 'programs', 'chrestomathy', 'polyglot'],
    project_urls={"GitHub": "https://github.com/discretegames/runmany",
                  "PyPI": "https://pypi.org/project/run-many",
                  "TestPyPI": "https://test.pypi.org/project/run-many"},
    python_requires='>=3.6',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Interpreters",
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Utilities",
        "Typing :: Typed",
        "Programming Language :: Python :: 3",
    ],
    entry_points={
        'console_scripts': [
            'runmany = run_many.run_many:main'
        ]
    },
)