# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring # TODO

import platform
from itertools import chain
from typing import Any, Tuple, Dict, List, Optional
from runmany.util import print_err, load_default_settings, NAME_KEY


def normalize(language_name: str) -> str:
    return language_name.strip()


def make_language_dict(language_list: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    language_dict: Dict[str, Any] = {}
    for language in language_list:
        if NAME_KEY not in language:
            print_err(f'No "{NAME_KEY}" key found for {language}. Skipping language.')
            continue
        language[NAME_KEY] = normalize(language[NAME_KEY])
        language_dict[language[NAME_KEY]] = language
    return language_dict


class Language:  # pylint: disable=too-few-public-methods
    def __init__(self, language_dict: Dict[str, Any], parent: 'NewSettings') -> None:
        self.dict = language_dict
        self.parent = parent

    def __getattr__(self, key: str) -> Any:
        if key in self.dict:
            return self.dict[key]
        return getattr(self.parent, key)


class NewSettings:
    def __init__(self, provided_settings: Optional[Dict[str, Any]] = None, updatable: bool = True) -> None:
        self.default_settings = load_default_settings()
        self.updatable = updatable
        self.update(provided_settings or {}, True)

    def update(self, new_provided_settings: Dict[str, Any], force: bool = False) -> None:
        if force or self.updatable:
            self.dict = self.combine_settings(self.default_settings, new_provided_settings)

    def combine_settings(self, default_settings: Dict[str, Any], provided_settings: Dict[str, Any]) -> Dict[str, Any]:
        combined = {key: provided_settings.get(key, value) for key, value in default_settings.items()}
        for op_sys in ('', '_windows', '_linux', '_mac'):
            custom = 'languages' + op_sys
            supplied = 'supplied_' + custom
            combined[custom] = self.combine_lists(combined[custom], combined[supplied])
            del combined[supplied]
        return combined

    def combine_lists(self, custom: List[Dict[str, Any]], supplied: List[Dict[str, Any]]) -> Dict[str, Language]:
        custom_dict = make_language_dict(custom)
        supplied_dict = make_language_dict(supplied)
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

    def __getattr__(self, key: str) -> Any:  # "." is for retrieving base settings
        return self.dict[key]

    def __contains__(self, language_name: str) -> bool:  # "in" is for checking Language existence
        os_languages, languages = self.platform_language_dicts()
        return language_name in os_languages or language_name in languages

    def __getitem__(self, language_name: str) -> Language:  # "[ ]" is for retrieving Languages
        os_languages, languages = self.platform_language_dicts()
        return os_languages.get(language_name, languages[language_name])
