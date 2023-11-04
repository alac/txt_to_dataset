import random

from library.token_count import get_token_count
from library.settings_manager import settings
from library.hacks_dataset_specific import prompt_dict_to_style_string


def undo_hyphens(prompt):
    if "Write a scene where\n-" in prompt:
        prompt = prompt.replace("Write a scene where\n-", "Write a scene where: ")
        return prompt.replace("\n-", " ").replace("  ", " ")
    return prompt


def sort_keys(prompt_dict, warn_unexpected_keys=False):
    ordered_keys = settings.get_setting("prompt_format.json_key_order")
    unexpected_keys = [k for k in prompt_dict if k not in ordered_keys]
    if unexpected_keys and warn_unexpected_keys:
        print(f"Prompt Dictionary had unexpected keys: {unexpected_keys}")
        # raise ValueError(f"Prompt Dictionary had unexpected keys: {unexpected_keys}")

    new_dict = {}
    for key in ordered_keys:
        new_dict[key] = prompt_dict.get(key, None)

    for key in sorted(unexpected_keys):
        new_dict[key] = prompt_dict[key]

    return new_dict


def get_full_text_from_prompt_dict(prompt_dict):
    story = prompt_dict["story"]
    context = prompt_dict.get("context", None)
    if context:
        story = context + "\n" + story
    return story


def prepare_prompt_dict_for_row(prompt_dict):
    allowed_fields = settings.get_setting("prompt_format.allowed_fields")
    aliased_fields = {
        "sensory detail": {
            "low": "abstract",
            "medium": "selective",
            "high": "vivid sensory",
        }
    }

    new_dict = {}
    for field in prompt_dict:
        if field in allowed_fields:
            new_dict[field] = prompt_dict[field]
            if field in aliased_fields:
                if prompt_dict[field] not in [None, ""]:
                    new_dict[field] = aliased_fields[field].get(prompt_dict[field].lower(), prompt_dict[field].lower())
    return new_dict


def generate_dataset_row_from_prompt_dict(prompt_dict, drop_tags_prob=0.0, droppable_tags=[]):
    context = prompt_dict.get("context", None)
    story = prompt_dict.get("story", "")
    prompt = prompt_dict.get("prompt", "")
    prompt = undo_hyphens(prompt)

    none_value_keys = [k for k in prompt_dict if prompt_dict[k] is None]
    for key in none_value_keys:
        del prompt_dict[key]

    if drop_tags_prob != 0:
        for tag in droppable_tags:
            if random.random() < drop_tags_prob and tag in prompt_dict:
                del prompt_dict[tag]

    style = ""
    if settings.get_setting("hacks.use_prose_prompt"):
        style = prompt_dict_to_style_string(prompt_dict)
    else:
        items = [i for i in prompt_dict.items()]
        random.shuffle(items)
        for key, value in items:
            if not value:
                continue
            style += f"{key}: {value.lower()}. "

    length = ""
    if len(style) > 0:
        token_count = get_token_count(story)
        if token_count < 300:
            length = "short"
        elif token_count < 500:
            length = "medium"
        elif token_count < 800:
            length = "large"
        elif token_count < 1000:
            length = "huge"
        else:
            length = "massive"

    system_suffix = prompt_dict.get("system suffix", "")

    return prompt_dict, style.strip(), context, prompt, length, story, system_suffix


def parse_names(names_list: str) -> list[str]:
    # not comprehensive; we just want to exclude things like "The old man" and "unnamed protagonist"
    potential_names = names_list.split(",")
    names = []
    for name in potential_names:
        name_parts = name.split(" ")
        if any([p for p in name_parts if p == p.lower()]):
            continue
        names.append(name.strip())
    return names


def estimate_total_tokens(all_strs:list[str]):
    format_tokens = 50  # the isolated "### System..."
    return get_token_count("".join([s for s in all_strs if s is not None])) + format_tokens
