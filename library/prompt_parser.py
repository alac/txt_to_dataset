import random

from library.token_count import get_token_count
from library.settings_manager import settings
from library.hacks_dataset_specific import prompt_dict_to_style_string, undo_hyphens


def sort_keys(prompt_dict: dict, warn_unexpected_keys=False):
    ordered_keys = settings.get_setting("prompt_format.json_key_order")
    unexpected_keys = [k for k in prompt_dict if k not in ordered_keys]
    if unexpected_keys and warn_unexpected_keys:
        print(f"Prompt Dictionary had unexpected keys: {unexpected_keys}")

    new_dict = {}
    for key in ordered_keys:
        new_dict[key] = prompt_dict.get(key, None)

    for key in sorted(unexpected_keys):
        new_dict[key] = prompt_dict[key]

    return new_dict


def get_full_text_from_prompt_dict(prompt_dict: dict):
    story = prompt_dict["story"]
    context = prompt_dict.get("context", None)
    if context:
        story = context + "\n" + story
    return story


def prepare_prompt_dict_for_row(prompt_dict: dict):
    allowed_fields = settings.get_setting("prompt_format.allowed_fields")

    new_dict = {}
    for field in prompt_dict:
        if field in allowed_fields:
            new_dict[field] = prompt_dict[field]
    return new_dict


def generate_dataset_row_from_prompt_dict(prompt_dict: dict, drop_tags_prob: float, droppable_tags: list):
    for field in settings.get_setting("prompt_format.replace_unicode_quotes_fields"):
        val = prompt_dict.get(field, None)
        if val:
            prompt_dict[field] = val.replace("\u201d", "\"").replace("\u201c", "\"")

    context = prompt_dict.get("context", None)
    story = prompt_dict.get("story", "")
    prompt = prompt_dict.get("prompt", "")

    if settings.get_setting("hacks.undo_hyphens_in_prompt"):
        prompt = undo_hyphens(prompt)

    none_value_keys = [k for k in prompt_dict if prompt_dict[k] is None]
    for key in none_value_keys:
        del prompt_dict[key]

    if drop_tags_prob != 0:
        for tag in droppable_tags:
            if random.random() < drop_tags_prob and tag in prompt_dict:
                del prompt_dict[tag]

    style = ""
    if settings.get_setting("hacks.use_prose_styles"):
        style = prompt_dict_to_style_string(prompt_dict)
    else:
        items = [i for i in prompt_dict.items()]
        random.shuffle(items)
        for key, value in items:
            if key in ["context", "story", "prompt"] or not value:
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
    if len(names_list) == 0:
        return []

    potential_names = names_list.split(",")
    names = []
    for name in potential_names:
        name_parts = name.split(" ")
        if any([p for p in name_parts if p == p.lower()]):
            continue
        names.append(name.strip())
    return names


def estimate_total_tokens(all_strs: list[str]):
    format_tokens = 50  # the isolated "### System..."
    return get_token_count("".join([s for s in all_strs if s is not None])) + format_tokens
