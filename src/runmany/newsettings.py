# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring # TODO

from typing import Any, Dict


class SettingsDict:
    def __init__(self, settings_dict: Dict[str, Any]) -> None:
        self.settings_dict = settings_dict


class Language:
    pass


class NewSettings:
    def __init__(self, default_settings: SettingsDict, provided_settings: SettingsDict, updatable: bool) -> None:
        self.default_settings = default_settings
        self.provided_settings = provided_settings
        self.updatable = updatable

    def update(self, new_provided_settings: SettingsDict) -> None:
        if self.updatable:
            self.provided_settings = new_provided_settings

    def language(self, language_name: str) -> Language:
        pass
