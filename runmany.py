import os
import io
import json
import tempfile
import subprocess

LANG_SEP_START, LANG_SEP_END = '~~~|', '|~~~'
DEFAULT_LANGUAGES_JSON = 'languages.json'
FILENAME_PLACEHOLDER = '$file'


def get_language_commands(language_json_data):
    command = language_json_data.get('command')
    if command is None:
        return {}
    names = []
    if "name" in language_json_data:
        names.append(language_json_data["name"])
    names.extend(language_json_data.get("other_names", []))
    return {name.strip().lower(): command for name in names}


def get_commands_dict(commands_dict):
    if commands_dict is None:
        with open(DEFAULT_LANGUAGES_JSON) as f:
            commands_dict = {}
            for language in json.load(f).get("languages", []):
                for name, command in get_language_commands(language).items():
                    if name not in commands_dict:
                        commands_dict[name] = command
    return commands_dict


def runone(language, command, snippet):
    print(f"{LANG_SEP_START} {language} {LANG_SEP_END}")
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
        tmp.write(snippet)
        tmp_filename = tmp.name
    if FILENAME_PLACEHOLDER in command:
        command = command.replace(FILENAME_PLACEHOLDER, f'"{tmp_filename}"')
    else:
        command += f' "{tmp_filename}"'
    try:
        subprocess.check_call(command)
        return True
    except subprocess.CalledProcessError:
        return False
    finally:
        os.remove(tmp_filename)


def runmany(manyfile, string=False, commands_dict=None):
    def tryrun():
        nonlocal snippets, runs, successes
        if language is not None:
            snippets += 1
            if language.lower() in commands_dict:
                runs += 1
                if runone(language, commands_dict[language.lower()], ''.join(snippet_lines)):
                    successes += 1

    snippets, runs, successes = 0, 0, 0
    commands_dict = get_commands_dict(commands_dict)

    with (io.StringIO if string else open)(manyfile) as f:
        language = None
        snippet_lines = []
        for line in f:
            stripped = line.strip()
            if stripped.startswith(LANG_SEP_START) and stripped.endswith(LANG_SEP_END):
                tryrun()
                language = stripped[len(LANG_SEP_START):-len(LANG_SEP_END)].strip()
                snippet_lines.clear()
            elif language is not None:
                snippet_lines.append(line)
        tryrun()
    print(f"{LANG_SEP_START} {snippets} , {runs}, {successes} {LANG_SEP_END}")


if __name__ == "__main__":
    runmany('helloworld.many')
    print('DONE')


# TODO
# detect command errors like "pyton" unrecognized
# rewrite so the result is a generator over (language, output string) pairs
# way to comment out a snippet !~~~|?
# argv
# stdin
# add other 7 languages to languages.json
# number the runs
