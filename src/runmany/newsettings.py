# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring # TODO

from runmany.util import JsonLike


class SettingsDict:
    def __init__(self, settings_json: JsonLike) -> None:
        pass

        # todo do json none, empty string checking here


class Language:
    pass


class NewSettings:
    def __init__(self, default_settings: JsonLike, provided_settings: JsonLike) -> None:
        self.default_settings = SettingsDict(default_settings)
        self.provided_settings = SettingsDict(provided_settings)
        self.updatable = provided_settings not in (None, '')

    def update(self, new_provided_settings: JsonLike) -> None:
        if self.updatable:
            self.provided_settings = SettingsDict(new_provided_settings)

    def language(self, language_name: str) -> Language:
        pass
