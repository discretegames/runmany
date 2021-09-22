
"""Package setup file for the Python 3 runmany package: https://pypi.org/project/runmany"""

from setuptools import setup, find_packages
from pathlib import Path

version = "0.7.3"

if __name__ == '__main__':
    with open(Path(__file__).with_name('README.md'), encoding='utf-8') as file:
        long_description = file.read()

    setup(
        name='runmany',
        version=version,
        author='discretegames',
        author_email='discretizedgames@gmail.com',
        description="A tool to run many programs written in many languages from one file.",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url='https://github.com/discretegames/runmany',
        packages=find_packages('src'),
        package_dir={'': 'src'},
        package_data={'': ['*.json', 'py.typed']},
        zip_safe=False,
        license="MIT",
        keywords=['run', 'execute', 'other languages', 'multiple languages', 'manyfile',
                  '.many', 'one file', 'programs', 'chrestomathy', 'polyglot'],
        project_urls={"GitHub": "https://github.com/discretegames/runmany",
                      "PyPI": "https://pypi.org/project/runmany",
                      "TestPyPI": "https://test.pypi.org/project/runmany"},
        python_requires='>=3.6',
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Education",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Topic :: Software Development :: Interpreters",
            "Topic :: Software Development :: Compilers",
            "Topic :: Software Development :: Build Tools",
            "Topic :: Utilities",
            "Typing :: Typed",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10"
        ],
        entry_points={
            'console_scripts': [
                'runmany = runmany.runmany:main'
            ]
        },
    )
