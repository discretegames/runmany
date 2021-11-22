"""RunMany settings module. Contains classes and functions for loading and handling the Settings object."""

import json
import pathlib
import platform
from itertools import chain
from typing import Any, Tuple, Dict, List, Set, Optional, cast
from runmany.util import JsonLike, print_err, set_show_errors


def load_default_settings() -> Dict[str, Any]:
    with open(pathlib.Path(__file__).with_name('default_settings.json'), encoding='utf-8') as file:
        return cast(Dict[str, Any], json.load(file))


def load_json_settings(settings: JsonLike, from_string: bool = False) -> Dict[str, Any]:
    if settings in (None, ''):
        return {}
    if isinstance(settings, dict):
        return settings
    if any(isinstance(settings, t) for t in (list, int, float, bool)):
        print_err(f'JSON base type must be dict or string, not {type(settings).__name__}. Using default settings JSON.')
        return {}
    if from_string:
        try:
            # Recursively call load in case JSON is a string filepath.
            return load_json_settings(json.loads(cast(str, settings)))
        except Exception as error:  # pylint: disable=broad-except # (JSONDecodeError misses a few things.)
            print_err(f'Embedded JSON issue "{error}". Using default settings JSON.')
    else:
        try:
            with open(cast(str, settings), encoding='utf-8') as file:
                return load_json_settings(json.load(file))
        except Exception as error:  # pylint: disable=broad-except
            print_err(f'JSON file issue "{error}". Using default settings JSON.')
    return {}


class Language:
    def __init__(self, language_dict: Dict[str, Any], parent: 'Settings') -> None:
        self.dict = language_dict
        self.parent = parent

    def __getattr__(self, key: str) -> Any:
        if key in self.dict:
            return self.dict[key]
        return getattr(self.parent, key)

    @staticmethod
    def normalize(language_name: str) -> str:
        return language_name.strip().lower()

    def __str__(self) -> str:
        return str(self.dict)

    def __repr__(self) -> str:
        return repr(self.dict)


class Settings:
    def __init__(self, provided_settings: Optional[Dict[str, Any]] = None, updatable: bool = True) -> None:
        self.default_settings = load_default_settings()
        self.updatable = updatable
        self.update(provided_settings or {}, True)

    def update(self, new_provided_settings: Dict[str, Any], force: bool = False) -> None:
        if force or self.updatable:
            self.dict = self.combine_settings(self.default_settings, new_provided_settings)
            set_show_errors(self.show_errors)

    def combine_settings(self, default_settings: Dict[str, Any], provided_settings: Dict[str, Any]) -> Dict[str, Any]:
        combined = {key: provided_settings.get(key, value) for key, value in default_settings.items()}
        for op_sys in ('', '_windows', '_linux', '_mac'):
            custom = 'languages' + op_sys
            supplied = 'supplied_' + custom
            combined[custom] = self.combine_lists(combined[custom], combined[supplied])
            del combined[supplied]
        return combined

    def combine_lists(self, custom: List[Dict[str, Any]], supplied: List[Dict[str, Any]]) -> Dict[str, Language]:
        custom_dict = self.make_language_dict(custom)
        supplied_dict = self.make_language_dict(supplied)
        combined: Dict[str, Language] = {}
        for name in chain(custom_dict, supplied_dict):
            if name not in combined:
                combined[name] = self.combine_languages(custom_dict.get(name, {}), supplied_dict.get(name, {}))
        return combined

    def combine_languages(self, custom: Dict[str, Any], supplied: Dict[str, Any]) -> Language:
        return Language({key: custom.get(key, supplied[key]) for key in chain(custom, supplied)}, self)

    def platform_language_dicts(self) -> Tuple[Dict[str, Language], Dict[str, Language]]:
        key = 'languages'
        platforms = {'windows': '_windows', 'linux': '_linux', 'darwin': '_mac'}
        os_key = key + platforms.get(platform.system().lower(), '')
        return getattr(self, os_key), getattr(self, key)

    def all_language_names(self) -> Set[str]:
        names: Set[str] = set()
        return names.union(self.languages, self.languages_windows, self.languages_linux, self.languages_mac)

    def __getattr__(self, key: str) -> Any:  # "." is for retrieving base settings
        return self.dict[key]

    def __contains__(self, language_name: str) -> bool:  # "in" is for checking Language existence
        os_languages, languages = self.platform_language_dicts()
        return language_name in os_languages or language_name in languages

    def __getitem__(self, language_name: str) -> Language:  # "[ ]" is for retrieving Languages
        os_languages, languages = self.platform_language_dicts()
        language_name = Language.normalize(language_name)
        return os_languages.get(language_name, languages[language_name])

    @staticmethod
    def make_language_dict(language_list: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        name_key = 'name'
        language_dict: Dict[str, Any] = {}
        for language in language_list:
            if name_key not in language:
                print_err(f'No "{name_key}" key found for {language}. Skipping language.')
                continue
            language[name_key] = language[name_key].strip()
            language_dict[Language.normalize(language[name_key])] = language
        return language_dict

    @staticmethod
    def from_json(settings: JsonLike) -> 'Settings':
        return Settings(load_json_settings(settings), settings is None)

    def update_with_json(self, raw_settings_json: str) -> None:
        if self.updatable:
            self.update(load_json_settings(raw_settings_json, from_string=True))

    def __str__(self) -> str:
        return str((self.updatable, self.dict))

    def __repr__(self) -> str:
        return repr((self.updatable, self.dict))
