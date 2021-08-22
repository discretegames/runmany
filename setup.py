from os import path
from setuptools import setup, find_packages

version = "0.0.9"

directory = path.abspath(path.dirname(__file__))
with open(path.join(directory, 'README.md'), encoding='utf-8') as file:
    long_description = file.read()

setup(
    name='run_many',
    version=version,
    author='discretegames',
    author_email='discretizedgames@gmail.com',
    description="Tool to run many programs written in many languages from one file.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/discretegames/runmany',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    package_data={'run_many': ['default_languages.json']},
    license="MIT",
    keywords=['python', 'data structure', 'algorithm', 'dsa'],
    project_urls={"GitHub": "https://github.com/discretegames/runmany",
                  "PyPI": "https://pypi.org/project/runmany",
                  "TestPyPI": "https://test.pypi.org/project/runmany"},
    python_requires='>=3.6',
    # todo keywords
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
    ]
)
