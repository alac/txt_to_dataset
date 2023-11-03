"""
inject_hardcoded_keys is for jamming in information manually on a 'story' level.
for now, this means the name of the author.
"""

import os
import json

from library.prompt_parser import sort_keys


class ValueEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, dict):
            return sorted(obj.items(), key=lambda x: x[1])
        else:
            return super().default(obj)


def populate_story_settings(all_in_folders):
    updated_story_settings = []

    for in_folder in all_in_folders:
        all_folders = []
        for sub_folder in os.listdir(in_folder):
            if os.path.isdir(os.path.join(in_folder, sub_folder)):
                all_folders.append(sub_folder)
        STORY_SETTINGS_FP = os.path.join(in_folder, "STORY_SETTINGS.json")
        if not os.path.exists(STORY_SETTINGS_FP):
            with open(STORY_SETTINGS_FP, "w", encoding='utf-8') as f:
                f.write("{}")
        with open(STORY_SETTINGS_FP, "r+", encoding='utf-8') as f:
            story_settings = json.load(f)
            to_add = [folder for folder in all_folders if folder not in story_settings]
            if to_add:
                for folder in to_add:
                    story_settings[folder] = {}
                for folder in story_settings:
                    story_settings[folder]["author"] = story_settings[folder].get("author", "")
                    story_settings[folder]["system suffix"] = story_settings[folder].get("system suffix", "")
                f.seek(0)
                json.dump(story_settings, f, indent=2, cls=ValueEncoder)
                updated_story_settings.append(STORY_SETTINGS_FP)

    if updated_story_settings:
        print(f"Updated story settings files ", updated_story_settings)
        raise ValueError("Update story_settings")


def process_folder(in_folder, out_folder):
    STORY_SETTINGS_FP = os.path.join(in_folder, "STORY_SETTINGS.json")
    with open(STORY_SETTINGS_FP, "r+", encoding='utf-8') as f:
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
