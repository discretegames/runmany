import os
import io
import json
import tempfile
import subprocess

LANG_START, LANG_END, LANG_SEP = '~~~|', '|~~~', '|'
STDIN_START, STDIN_END, STDIN_SEP = '$$$|', '|$$$', '$$$|$$$'
ARGV_START, ARGV_END, ARGV_SEP = '@@@', '|@@@', '@@@|@@@'

ALL_KEY = 'all'
LANGUAGES_KEY = 'languages'
STRIP_BLANK_LINES_KEY = 'strip_blank_lines'
FILE_PLACEHOLDER, ARGV_PLACEHOLDER = '$file', '$argv'
FILE_MISSING_APPEND = f' {FILE_PLACEHOLDER}'
ARGV_MISSING_APPEND = f' {ARGV_PLACEHOLDER}'

DEFAULT_LANGUAGES_JSON = 'default_languages.json'
BACKUP_LANGUAGES_JSON = {
    ALL_KEY: "All",
    LANGUAGES_KEY: {
        "Python": "python"
    },
    STRIP_BLANK_LINES_KEY: True
}


def to_file_like(x: int, y: int) -> str:
    x = z
    return ''*8


# class RunMany:
#     def __init__(self, manyfile, languages_json=None, string=False, string_json=False):
#         if x == None:
#             print('foo')
#         pass

# runmany works for filename or file handle
# runmanys works for strings - meh


# if __name__ == "__main__":
#     RunMany('')


# def get_language_commands(language_json_data):
#     command = language_json_data.get('command')
#     if command is None:
#         return {}
#     names = []
#     if "name" in language_json_data:
#         names.append(language_json_data["name"])
#     names.extend(language_json_data.get("other_names", []))
#     return {name.strip().lower(): command for name in names}


# def get_commands_dict(commands_dict):
#     if commands_dict is None:
#         with open(DEFAULT_LANGUAGES_JSON) as f:
#             commands_dict = {}
#             for language in json.load(f).get("languages", []):
#                 for name, command in get_language_commands(language).items():
#                     if name not in commands_dict:
#                         commands_dict[name] = command
#     return commands_dict


# def runone(language, command, snippet):
#     print(f"{LANG_START} {language} {LANG_END}")
#     with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
#         tmp.write(snippet)
#         tmp_filename = tmp.name
#     if FILENAME_PLACEHOLDER in command:
#         command = command.replace(FILENAME_PLACEHOLDER, f'"{tmp_filename}"')
#     else:
#         command += f' "{tmp_filename}"'
#     try:
#         subprocess.check_call(command)
#         return True
#     except subprocess.CalledProcessError:
#         return False
#     finally:
#         os.remove(tmp_filename)


# def runmany(manyfile, string=False, commands_dict=None):
#     def tryrun():
#         nonlocal snippets, runs, successes
#         if language is not None:
#             snippets += 1
#             if language.lower() in commands_dict:
#                 runs += 1
#                 if runone(language, commands_dict[language.lower()], ''.join(snippet_lines)):
#                     successes += 1

#     snippets, runs, successes = 0, 0, 0
#     commands_dict = get_commands_dict(commands_dict)

#     with (io.StringIO if string else open)(manyfile) as f:
#         language = None
#         snippet_lines = []
#         for line in f:
#             stripped = line.strip()
#             if stripped.startswith(LANG_START) and stripped.endswith(LANG_END):
#                 tryrun()
#                 language = stripped[len(LANG_START):-len(LANG_END)].strip()
#                 snippet_lines.clear()
#             elif language is not None:
#                 snippet_lines.append(line)
#         tryrun()
#     print(f"{LANG_START} {snippets} , {runs}, {successes} {LANG_END}")


# if __name__ == "__main__":
#     runmany('helloworld.many')
#     print('DONE')
