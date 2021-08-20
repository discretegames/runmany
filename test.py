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

# 518 lines before

JsonLike = Union[None, str, bytes, 'os.PathLike[Any]', Any]
DEFAULT_LANGUAGES_JSON_FILE = 'default_languages.json'


def json_to_class(json_string: str) -> Any:
    return json.loads(json_string, object_hook=lambda d: types.SimpleNamespace(**d))


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
    def normalize(language: str) -> str:
        return language.strip().lower()

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
        elif LanguagesData.normalize(language_obj.name) == LanguagesData.normalize(all_name):
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

        self.dict: Dict[str, LanguageData] = {}
        for language_obj in itertools.chain(self.default_languages, self.languages):
            if self.language_obj_valid(language_obj, self.all_name):
                self.dict[self.normalize(language_obj.name)] = LanguageData(language_obj, self)

    def __getattr__(self, name: str) -> Any:
        if hasattr(self.settings, name):
            return getattr(self.settings, name)
        return getattr(self.defaults, name)

    def __getitem__(self, language: str) -> Any:
        return self.dict[self.normalize(language)]

    def unpack(self, language: str) -> List[str]:
        language = self.normalize(language)
        if language == self.normalize(self.all_name):
            return list(self.dict.keys())
        return [language]


# todo pass this around, not languages_data
class LanguageData:
    def __init__(self, language_obj: Any, parent: LanguagesData):
        self.obj = language_obj
        self.parent = parent

    def __getattr__(self, name: str) -> Any:
        if hasattr(self.obj, name):
            return getattr(self.obj, name)
        return getattr(self.parent, name)


ld = LanguagesData({"stderr": "never"})

x = ld['C']
print(x.stderr)
