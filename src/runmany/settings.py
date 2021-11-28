"""RunMany settings module. Contains classes and functions for loading and handling the Settings object."""

import json
import pathlib
import platform
from itertools import chain
from typing import Any, Dict, List, Optional, cast
from runmany.util import JsonLike, print_err, set_show_errors


PLATFORMS = {'windows': 'windows', 'linux': 'linux', 'darwin': 'mac'}


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
        return str(self.dict)  # pragma: no cover

    def __repr__(self) -> str:
        return repr(self.dict)  # pragma: no cover


class Settings:
    def __init__(self, provided_settings: Optional[Dict[str, Any]] = None, updatable: bool = True) -> None:
        self.default_settings = load_default_settings()
        self.updatable = updatable
        self.update(provided_settings or {})

    def update(self, new_provided_settings: Dict[str, Any]) -> None:
        try:
            self.dict = self.combine_settings(self.default_settings, new_provided_settings)
        except Exception as error:  # pylint: disable=broad-except
            print_err(f'Issue combining JSONs "{error}". Something may be the wrong type. Using default settings JSON.')
            self.dict = self.combine_settings(self.default_settings, {})

        set_show_errors(self.show_errors)

    def combine_settings(self, default_settings: Dict[str, Any], provided_settings: Dict[str, Any]) -> Dict[str, Any]:
        combined = {key: provided_settings.get(key, value) for key, value in default_settings.items()}
        languages_key, supplied_key = 'languages', 'supplied_languages'

        supplied_languages = self.make_language_dict(combined[supplied_key])
        languages = self.make_language_dict(combined[languages_key])

        if self.has_os():  # pragma: no cover
            supplied_languages_os = self.make_language_dict(combined[self.with_os(supplied_key)])
            supplied_languages = self.combine_dicts(supplied_languages_os, supplied_languages)

            languages_os = self.make_language_dict(combined[self.with_os(languages_key)])
            languages = self.combine_dicts(languages_os, languages)

        computed_languages = self.combine_dicts(languages, supplied_languages)
        combined['computed_languages'] = {name: Language(value, self) for name, value in computed_languages.items()}
        return combined

    def computed_languages(self) -> Dict[str, Language]:
        return cast(Dict[str, Language], self.dict['computed_languages'])

    @staticmethod
    def combine_dicts(new: Dict[str, Dict[str, Any]], base: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        combined: Dict[str, Dict[str, Any]] = {}
        for name in chain(base, new):
            if name not in combined:
                combined[name] = {}
                new_language, base_language = new.get(name, {}), base.get(name, {})
                for key in chain(base_language, new_language):
                    combined[name][key] = new_language.get(key, base_language.get(key))
        return combined

    def __getattr__(self, key: str) -> Any:  # "." is for retrieving base settings
        return self.dict[key]

    def __contains__(self, language_name: str) -> bool:  # "in" is for checking Language existence
        return Language.normalize(language_name) in self.computed_languages()

    def __getitem__(self, language_name: str) -> Language:  # "[ ]" is for retrieving Languages
        return self.computed_languages()[language_name]

    @staticmethod
    def with_os(key: str) -> str:
        return f'{key}_{PLATFORMS.get(platform.system().lower().strip(), "unknown")}'

    @staticmethod
    def has_os() -> bool:
        return platform.system().lower().strip() in PLATFORMS

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
        return str((self.updatable, self.dict))  # pragma: no cover

    def __repr__(self) -> str:
        return repr((self.updatable, self.dict))  # pragma: no cover
