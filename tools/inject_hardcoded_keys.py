"""
inject_hardcoded_keys is for manually setting values in a folder structure like /group/story/chunk.json.
setting is done on a story level, so that you can set the 'author' or 'genre' manually.
"""

import os
import json
import argparse

from library.prompt_parser import sort_keys


INJECTION_SETTINGS_FILE = "INJECTION_SETTINGS.json"


class ValueEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, dict):
            return sorted(obj.items(), key=lambda x: x[1])
        else:
            return super().default(obj)


def populate_story_settings(all_in_folders, keys):
    updated_story_settings = []

    for in_folder in all_in_folders:
        all_folders = []
        for sub_folder in os.listdir(in_folder):
            if os.path.isdir(os.path.join(in_folder, sub_folder)):
                all_folders.append(sub_folder)
        injection_settings_fp = os.path.join(in_folder, INJECTION_SETTINGS_FILE)
        if not os.path.exists(injection_settings_fp):
            with open(injection_settings_fp, "w", encoding='utf-8') as f:
                f.write("{}")
        with open(injection_settings_fp, "r+", encoding='utf-8') as f:
            story_settings = json.load(f)
            to_add = [folder for folder in all_folders if folder not in story_settings]
            if to_add:
                for folder in to_add:
                    story_settings[folder] = {}
                for folder in story_settings:
                    for key in keys:
                        story_settings[folder]["key"] = story_settings[folder].get("key", "")
                f.seek(0)
                json.dump(story_settings, f, indent=2, cls=ValueEncoder)
                updated_story_settings.append(injection_settings_fp)

    if updated_story_settings:
        raise ValueError(f"Update the story settings file with intended values: ", updated_story_settings)


def process_folder(in_folder, out_folder):
    injection_settings_fp = os.path.join(in_folder, INJECTION_SETTINGS_FILE)
    with open(injection_settings_fp, "r+", encoding='utf-8') as f:
        story_settings = json.load(f)

    for sub_folder in os.listdir(in_folder):
        if os.path.isdir(os.path.join(in_folder, sub_folder)):
            process_story_folder(in_folder, sub_folder, out_folder, story_settings.get(sub_folder, None))


def process_story_folder(in_folder, sub_folder, out_folder, story_settings):
    source_folder = os.path.join(in_folder, sub_folder)
    story_folder = os.path.join(out_folder, sub_folder)

    os.makedirs(story_folder, exist_ok=True)

    for filename in os.listdir(source_folder):
        if not filename.endswith(".txt") or not os.path.isfile(os.path.join(source_folder, filename)):
            continue
        if os.path.exists(os.path.join(story_folder, filename)):
            print(f"skipping chunk: {source_folder}, {filename}")
            continue
        print(f"processing chunk: {source_folder}, {filename}")
        with open(os.path.join(source_folder, filename), "r", encoding='utf-8') as f:
            prompt_json = f.read()
        try:
            prompt_dict = json.loads(prompt_json)
        except json.decoder.JSONDecodeError:
            continue
        prompt_dict = apply_story_settings(prompt_dict, story_settings)
        with open(os.path.join(story_folder, filename), "w", encoding='utf-8') as f:
            f.writelines(json.dumps(sort_keys(prompt_dict), indent=4))


def apply_story_settings(prompt_dict, story_settings):
    for setting in story_settings:
        prompt_dict[setting] = story_settings[setting]
    return prompt_dict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        usage="""Allows adding key/value pairs to jsons in a double nested folder structure.
You'll run this script twice. The first time will create an INJECTION_SETTINGS.json in the input folder.
Edit the values in INJECTION_SETTINGS.json as desired:
{
  "The Bible": {              # "The Bible" is one of the subfoders of the input folder
    "genre": "religion"       # "genre" is a key to be added to every json in "The Bible"
  }
  "Encyclopedia Britannica": {
...
Then run the script a second time to populate the output_folder with the modified files.

python -m tools.inject_hardcoded_keys --input_folder in --output_folder out --keys test""")
    parser.add_argument('--input_folder', type=str, required=True, help='Input folder path. Should contain subfolders '
                        ' containing json files.')
    parser.add_argument('--output_folder', type=str, required=True, help='Output folder path. Will be populated by a '
                        ' mirrored structure as the input folder, with modified json files.')
    parser.add_argument('--keys', nargs='+', dest='keys', required=True, help='The keys to add.')
    args = parser.parse_args()

    populate_story_settings([args.input_folder], args.keys)
    process_folder(args.input_folder, args.output_folder)
