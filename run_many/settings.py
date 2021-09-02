import json
import types
import pathlib
from typing import Any, Dict, List

from .util import JsonLike, print_err, display_errors

DEFAULT_SETTINGS_JSON_FILE = 'default_settings.json'
ALL_NAME_KEY, NAME_KEY, COMMAND_KEY, EXT_KEY = 'all_name', 'name', 'command', 'ext'


class LanguageData:
    def __init__(self, language_obj: Any, parent: 'Settings') -> None:
        self.obj = language_obj
        self.default_obj = None
        self.parent = parent

    def update_obj(self, language_obj: Any) -> None:
        self.obj, self.default_obj = language_obj, self.obj

    def __getattr__(self, name: str) -> Any:
        if hasattr(self.obj, name):
            return getattr(self.obj, name)
        if hasattr(self.default_obj, name):
            return getattr(self.default_obj, name)
        return getattr(self.parent, name)


class Settings:
    @staticmethod
    def normalize(language: str) -> str:
        return language.strip().lower()

    @staticmethod
    def json_to_class(json_string: str) -> Any:
        return json.loads(json_string, object_hook=lambda d: types.SimpleNamespace(**d))

    @staticmethod
    def get_json_string(settings_json: JsonLike) -> str:
        if settings_json is None:
            return str({})
        elif isinstance(settings_json, dict):  # Assume already valid json dict.
            return json.dumps(settings_json)
        with open(settings_json) as file:  # Assume path like.
            return file.read() or str({})

    def language_obj_valid(self, language_obj: Any, is_default: bool) -> bool:
        end = ". Ignoring language."

        if not hasattr(language_obj, NAME_KEY):
            print_err(f'No "{NAME_KEY}" key found for json list item{end}')
            return False

        if Settings.normalize(language_obj.name) == Settings.normalize(self.all_name):
            print_err(f'Language name "{language_obj.name}" cannot match {ALL_NAME_KEY} "{self.all_name}"{end}')
            return False

        default_obj = self[language_obj.name] if not is_default and language_obj.name in self else None
        if not hasattr(language_obj, COMMAND_KEY) and not hasattr(default_obj, COMMAND_KEY):
            print_err(f'No "{COMMAND_KEY}" key found for {language_obj.name}{end}')
            return False

        return True

    def __init__(self, settings_json: JsonLike) -> None:
        self.data = self.json_to_class(self.get_json_string(settings_json))
        with open(pathlib.Path(__file__).with_name(DEFAULT_SETTINGS_JSON_FILE)) as file:
            self.default_data = self.json_to_class(file.read())
        global display_errors
        display_errors = self.show_errors

        self.dict: Dict[str, LanguageData] = {}
        for language_obj in self.default_languages:
            if self.language_obj_valid(language_obj, True):
                self[language_obj.name] = LanguageData(language_obj, self)

        for language_obj in self.languages:
            if self.language_obj_valid(language_obj, False):
                if language_obj.name in self:
                    self[language_obj.name].update_obj(language_obj)
                else:
                    self[language_obj.name] = LanguageData(language_obj, self)

    def __getattr__(self, name: str) -> Any:
        if hasattr(self.data, name):
            return getattr(self.data, name)
        return getattr(self.default_data, name)

    def __getitem__(self, language: str) -> Any:
        return self.dict[self.normalize(language)]

    def __setitem__(self, language: str, language_data: LanguageData) -> None:
        self.dict[self.normalize(language)] = language_data

    def __contains__(self, language: str) -> bool:
        return self.normalize(language) in self.dict

    def unpack(self, language: str) -> List[str]:
        language = self.normalize(language)
        if language == self.normalize(self.all_name):
            return list(self.dict.keys())
        if language in self:
            return [language]
        raise KeyError
