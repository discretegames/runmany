# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring # TODO


from itertools import chain
from typing import Any, Dict, List
from runmany.util import print_err, NAME_KEY


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
    def __init__(self, default_settings: Dict[str, Any], provided_settings: Dict[str, Any], updatable: bool) -> None:
        self.default_settings = default_settings
        self.updatable = updatable
        self.update(provided_settings, True)

    def update(self, new_provided_settings: Dict[str, Any], force: bool = False) -> None:
        if force or self.updatable:
            # TODO if new_provided_settings is a string, this is the place to load that from file
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

    #  TODO review everything below

    def __getattr__(self, key: str) -> Any:  # "." is for retrieving base settings
        return self.dict[key]

    def __contains__(self, language_name: str) -> bool:  # "in" is for checking Language existence
        return language_name in self.provided_settings

    def __getitem__(self, language_name: str) -> Language:  # "[ ]" is for retrieving Languages
        return self.provided_settings[language_name]
