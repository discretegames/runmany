import os
import io
import sys
import abc
import json
import enum
import types
import pathlib
import tempfile
import argparse
import itertools
import subprocess
import dataclasses
import collections
from typing import Any, List, DefaultDict, Tuple, Union, Optional, TextIO, Iterator, cast, Dict


'''things to handle

- stderr enum?
- language validation

        name = language_json[JsonKeys.NAME]
        if JsonKeys.NAME not in language_json:
            print_err(f'No "{JsonKeys.NAME}" key found in {json.dumps(language_json)}. Ignoring language.')
            return False
        if Language.normalize(name) == Language.normalize(all_name):
            print_err(f'Language name "{name}" cannot match {JsonKeys.ALL_NAME} "{all_name}". Ignoring language.')
            return False
        if JsonKeys.COMMAND not in language_json:
            print_err(f'No "{JsonKeys.COMMAND}" key found for {name}. Ignoring language.')
            return False
        if Placeholders.EXT in language_json[JsonKeys.COMMAND] and JsonKeys.EXT not in language_json:
            print_err(f'No "{JsonKeys.EXT}" key found to fill "{Placeholders.EXT}" placeholder for {name} command.'
                      ' Ignoring language.')

- unpack
- language lookup (with normalize)
- order of languages
    languages start to end
    then default_langs start to end


518 lines rn
will it be that much shorter this way? maybe


def load_languages_json(languages_json: Any) -> Any:
    if isinstance(languages_json, dict):
        return languages_json
    try:
        if languages_json is None:
            languages_json = pathlib.Path(__file__).resolve().parent.joinpath(DEFAULT_LANGUAGES_JSON_FILE)
        with open(os.fspath(languages_json)) as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError, TypeError):
        print_err(f'Unable to load json "{languages_json}". Using backup json with limited functionality.')
        return BACKUP_LANGUAGES_JSON

- test 3 json types None, file, or dict

'''
JsonLike = Union[None, str, bytes, 'os.PathLike[Any]', Any]
DEFAULT_LANGUAGES_JSON_FILE = 'default_languages.json'


def json_to_class(json_string: str) -> Any:
    return json.loads(json_string, object_hook=lambda d: types.SimpleNamespace(**d))


def normalize(language_name: str) -> str:
    return language_name.strip().lower()


def print_err(message: str) -> None:
    print(f"***| RunMany Error: {message} |***", file=sys.stderr)


ALL_NAME_KEY = 'all_name'
NAME_KEY = 'name'
EXT_KEY = 'ext'
COMMAND_KEY = 'command'


class Placeholders(abc.ABC):
    EXT = '$ext'


class LanguagesData:
    @staticmethod
    def get_json_string(languages_json: JsonLike) -> str:
        if languages_json is None:
            return str({})
        elif isinstance(languages_json, dict):  # Assume already valid json dict.
            return json.dumps(languages_json)
        with open(languages_json) as file:  # Assume path like.
            return file.read()

    @staticmethod
    def language_obj_valid(language_obj: Any, all_name: str) -> bool:
        msg = None
        if not hasattr(language_obj, NAME_KEY):
            msg = f'No "{NAME_KEY}" key found.'
        elif normalize(language_obj.name) == normalize(all_name):
            msg = f'Language name "{language_obj.name}" cannot match {ALL_NAME_KEY} "{all_name}".'
        elif not hasattr(language_obj, COMMAND_KEY):
            msg = f'No "{COMMAND_KEY}" key found for {language_obj.name}.'
        elif not hasattr(language_obj, EXT_KEY) and Placeholders.EXT in language_obj.command:
            msg = f'No "{EXT_KEY}" key found to fill "{Placeholders.EXT}" placeholder for {language_obj.name} command.'
        if msg:
            print_err(f'{msg} Ignoring language.')
            return False
        return True

    def __init__(self, languages_json: JsonLike) -> None:
        self.settings = json_to_class(self.get_json_string(languages_json))
        with open(DEFAULT_LANGUAGES_JSON_FILE) as file:
            self.defaults = json_to_class(file.read())

        self.dict: Dict[str, Any] = {}
        for language_obj in itertools.chain(self.default_languages, self.languages):
            if self.language_obj_valid(language_obj, self.all_name):
                self[language_obj.name] = language_obj
                # todo add getattr

    def __getattr__(self, name: str) -> Any:
        if hasattr(self.settings, name):
            return getattr(self.settings, name)
        return getattr(self.defaults, name)

    def __setitem__(self, language: str, language_obj: Any) -> None:
        self.dict[normalize(language)] = language_obj

    def __getitem__(self, language: str) -> Any:
        return self.dict[normalize(language)]

    # Todo
    # make dict of languages with validation
    # set up self.stderr with enum (getattr only triggers on not found)
    # ensure normalize used elsewhere
    # inherit timeout


ld = LanguagesData('languages.json')

print(ld[' C '])
