# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring # TODO

import platform
from typing import Any, Dict, List, Optional, Tuple
from runmany.util import print_err, NAME_KEY


def normalize(language_name: str) -> str:
    return language_name.strip()


class Language:  # pylint: disable=too-few-public-methods
    def __init__(self, language_dict: Dict[str, Any], parent: 'SettingsDict') -> None:
        self.dict = language_dict
        self.dict[NAME_KEY] = normalize(self.dict[NAME_KEY])
        self.parent = parent

    def __getattr__(self, key: str) -> Any:
        if key in self.dict:
            return self.dict[key]
        # if hasattr()
        # TODO! need to rework settings system as this won't easily work after :(

        return self.dict.get(key)  # TODO bubble up


class LanguageDict:
    def __init__(self, language_list: List[Dict[str, Any]], parent: 'SettingsDict'):
        self.dict: Dict[str, Language] = {}
        for language_dict in language_list:
            if NAME_KEY in language_dict:
                language = Language(language_dict, parent)
                self.dict[language.name] = language
            else:
                print_err(f'No "{NAME_KEY}" key found for {language_dict}. Skipping language.')

    def __contains__(self, language_name: str) -> bool:
        return normalize(language_name) in self.dict

    def __getitem__(self, language_name: str) -> Language:
        return self.dict[normalize(language_name)]


class SettingsDict:
    def __init__(self, settings_dict: Dict[str, Any], default: Optional['SettingsDict']) -> None:
        self.dict = settings_dict
        self.default = default
        self.language_dicts: Dict[str, LanguageDict] = {}
        for prefix in ('languages', 'supplied_languages'):
            for suffix in ('', '_windows', '_linux', '_mac'):
                self.set_language_dict(prefix + suffix)

    def set_language_dict(self, key: str) -> None:
        self.language_dicts[key] = LanguageDict(self.dict.get(key, []), self)

    def __getattr__(self, key: str) -> Any:
        return self.dict.get(key, getattr(self.default, key))

    def language_dicts_for_platform(self, supplied: bool) -> Tuple[LanguageDict, LanguageDict]:
        key = 'languages'
        suffix = {'windows': '_windows', 'linux': '_linux', 'darwin': '_mac'}[platform.system().lower()]
        os_key = key + suffix
        if supplied:
            key, os_key = key + 'supplied_', os_key + 'supplied_'
        return self.language_dicts[key], self.language_dicts[os_key]

    def __contains__(self, name: str) -> bool:
        try:
            _ = self[name]
            return True
        except KeyError:
            return False

    def __getitem__(self, language_name: str) -> Language:
        for supplied in (False, True):
            os_languages, languages = self.language_dicts_for_platform(supplied)
            if language_name in os_languages:
                return os_languages[language_name]
            if language_name in languages:
                return languages[language_name]
        if self.default:
            return self.default[language_name]
        raise KeyError


class NewSettings:
    def __init__(self, settings_dict: Dict[str, Any], default_settings_dict: Dict[str, Any], updatable: bool) -> None:
        self.default_settings = SettingsDict(default_settings_dict, None)
        self.provided_settings = SettingsDict(settings_dict, self.default_settings)
        self.updatable = updatable

    def update(self, new_settings_dict: Dict[str, Any]) -> None:
        if self.updatable:
            self.provided_settings = SettingsDict(new_settings_dict, self.default_settings)

    def __getattr__(self, key: str) -> Any:  # "." is for retrieving base settings
        return getattr(self.provided_settings, key)

    def __contains__(self, language_name: str) -> bool:  # "in" is for checking Language existence
        return language_name in self.provided_settings

    def __getitem__(self, language_name: str) -> Language:  # "[ ]" is for retrieving Languages
        return self.provided_settings[language_name]
