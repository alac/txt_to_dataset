import json
import random

from library.settings_manager import settings
from library.english_constants import titles
from library.prompt_parser import parse_names


female_names_cache = []
male_names_cache = []


def get_cached_names():
    if len(female_names_cache) == 0:
        with open("library/names_female.json", "r", encoding='utf-8') as f:
            female_names_cache.extend(json.load(f))
    if len(male_names_cache) == 0:
        with open("library/names_male.json", "r", encoding='utf-8') as f:
            male_names_cache.extend(json.load(f))
    return female_names_cache, male_names_cache


def randomize_names(prompt_dict):
    female_chars = parse_names(prompt_dict["female characters"])
    male_chars = parse_names(prompt_dict["male characters"])
    if len(male_chars) + len(female_chars) == 0:
        return prompt_dict, {}

    female_names, male_names = get_cached_names()
    new_first_names = random.sample(male_names, len(male_chars)) + random.sample(female_names, len(female_chars))
    new_last_names = random.sample(male_names, len(male_chars)) + random.sample(female_names, len(female_chars))
    original_names = male_chars + female_chars

    keys_with_content = settings.get_setting("randomize_names.keys_containing_names")

    all_replacements = {}
    for index, old_name in enumerate(original_names):
        name_parts = old_name.split(" ")
        first_name = name_parts[0]
        last_name = ""
        if len(name_parts) == 2:
            last_name = name_parts[1]

        if name_parts:
            if first_name in titles:
                first_name = ""
            elif first_name.endswith("'s"):
                first_name = first_name[:-2]
                last_name = ""
            elif first_name in settings.get_setting("randomize_names.randomization_blacklist"):
                first_name = ""
                last_name = ""

        swaps = [(first_name, new_first_names[index]), (last_name, new_last_names[index])]
        modded_name = old_name
        for old, new in swaps:
            if len(old):
                modded_name = modded_name.replace(old, new)
        all_replacements[old_name] = modded_name

        for old, new in swaps:
            if len(old) == 0:
                continue

            def stutter(n):
                return f"{n[0]}-{n}"

            for oldA, newA in [(old, new), (old.upper(), new.upper()), (stutter(old), stutter(new))]:
                for k in keys_with_content:
                    if k in prompt_dict and prompt_dict.get(k, None) is not None:
                        prompt_dict[k] = prompt_dict[k].replace(oldA, newA)
    return prompt_dict, all_replacements
