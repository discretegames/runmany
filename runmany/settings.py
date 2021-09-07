import json
import types
import pathlib
from typing import Any, Dict, List, Union, cast
from runmany.util import JsonLike, print_err, set_show_errors

DEFAULT_SETTINGS_JSON_FILE = 'default_settings.json'
ALL_NAME_KEY, NAME_KEY, COMMAND_KEY, EXT_KEY = 'all_name', 'name', 'command', 'ext'


def normalize(language: str) -> str:
    return language.strip().lower()


def json_to_class(json_string: str) -> Any:
    return json.loads(json_string, object_hook=lambda d: types.SimpleNamespace(**d))


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
    def __init__(self, settings_json_string: str) -> None:
        self.data = json_to_class(settings_json_string)
        with open(pathlib.Path(__file__).with_name(DEFAULT_SETTINGS_JSON_FILE)) as file:
            self.default_data = json_to_class(file.read())
        set_show_errors(self.show_errors)

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

    def language_obj_valid(self, language_obj: Any, is_default: bool) -> bool:
        end = ". Ignoring language."

        if not hasattr(language_obj, NAME_KEY):
            print_err(f'No "{NAME_KEY}" key found for json list item{end}')
            return False

        if normalize(language_obj.name) == normalize(self.all_name):
            print_err(f'Language name "{language_obj.name}" cannot match {ALL_NAME_KEY} "{self.all_name}"{end}')
            return False

        default_obj = self[language_obj.name] if not is_default and language_obj.name in self else None
        if not hasattr(language_obj, COMMAND_KEY) and not hasattr(default_obj, COMMAND_KEY):
            print_err(f'No "{COMMAND_KEY}" key found for {language_obj.name}{end}')
            return False

        return True

    def __getattr__(self, name: str) -> Any:
        if hasattr(self.data, name):
            return getattr(self.data, name)
        return getattr(self.default_data, name)

    def __getitem__(self, language: str) -> Any:
        return self.dict[normalize(language)]

    def __setitem__(self, language: str, language_data: LanguageData) -> None:
        self.dict[normalize(language)] = language_data

    def __contains__(self, language: str) -> bool:
        return normalize(language) in self.dict

    def unpack(self, language: str) -> List[str]:
        language = normalize(language)
        if language == normalize(self.all_name):
            return list(self.dict.keys())
        if language in self:
            return [language]
        raise KeyError


def json_err(error: Union[str, Exception]) -> None:
    print_err(f'JSON issue - {error}. Using default settings JSON.')


def load_settings(provided_json: JsonLike, hardcoded_json_string: str) -> Settings:
    settings_json_string = ''
    if provided_json is None:
        settings_json_string = hardcoded_json_string
    else:
        if isinstance(provided_json, dict):
            try:
                settings_json_string = json.dumps(provided_json)
            except (TypeError, ValueError) as e:
                json_err(e)
        else:
            try:
                with open(provided_json) as file:
                    settings_json_string = file.read()
            except IOError as e:
                json_err(e)

    try:  # Validate settings_json_string.
        if not isinstance(json.loads(settings_json_string.strip() or str({})), dict):
            json_err('The JSON must be an object/dict')
    except json.decoder.JSONDecodeError as e:
        json_err(e)
        settings_json_string = str({})

    return Settings(settings_json_string.strip() or str({}))
