import json
import types


def json_to_class(file):
    with open(file) as f:
        return json.load(f, object_hook=lambda d: types.SimpleNamespace(**d))


'''things to handle

- stderr enum?
- language validation
- language lookup (with normalize)
- order of languages
    languages start to end
    then default_langs start to end


518 lines rn
will it be that much shorter this way? maybe

'''


class LanguagesData:
    def __init__(self):
        self.settings = json_to_class('languages.json')
        self.defaults = json_to_class('default_languages.json')

    def __getattr__(self, name):
        if hasattr(self.settings, name):
            return getattr(self.settings, name)
        return getattr(self.defaults, name)


ld = LanguagesData()

print(ld.timeout, ld.show_code)
