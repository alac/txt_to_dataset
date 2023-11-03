import json
import random
from library.token_count import get_token_count
from library.settings_manager import settings


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
        "sensory detail" : {
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
                new_dict[field] = aliased_fields[field].get(prompt_dict[field], prompt_dict[field])
    return new_dict


def generate_dataset_row_from_prompt_dict(prompt_dict, use_key_value=False, drop_tags_prob=0.0):
    context = prompt_dict.get("context", None)
    story = prompt_dict.get("story", "")
    prompt = prompt_dict.get("prompt", "")
    prompt = undo_hyphens(prompt)

    if context:
        context = context.replace("*** ", "***\n")
    story = story.replace("*** ", "***\n")

    none_value_keys = [k for k in prompt_dict if prompt_dict[k] is None]
    for key in none_value_keys:
        del prompt_dict[key]

    if drop_tags_prob != 0:
        # only drop tags that very likely to be present
        # style_tags = ['tone', 'writing style', 'pacing', 'sensory detail', 'point of view', 'author']
        style_tags = ['tone', 'writing style', 'genre', 'humor quality', 'pacing', 'sensory detail', 'author']
        for tag in style_tags:
            if random.random() < drop_tags_prob and tag in prompt_dict:
                del prompt_dict[tag]

    style = ""
    if not use_key_value and prompt_dict.get('point of view', False):
        tags_line = ""
        if prompt_dict.get('tone', None) not in [None, ""]:
            tags_line += f" Tone: {prompt_dict['tone'].lower()}."
        if prompt_dict.get('writing style', None) not in [None, ""]:
            tags_line += f" Writing Style: {prompt_dict['writing style'].lower()}."
        if prompt_dict.get('genre', None) not in [None, ""]:
            tags_line += f" Genre: {prompt_dict['genre'].lower()}."
        tags_line = tags_line.replace("..", ".")

        description = ""
        if prompt_dict.get('humor quality', '').lower() == "high":
            description += "Humorously written "
        else:
            description += "Written "
        if prompt_dict.get('pacing', None) not in [None, ""]:
            description += f"with {prompt_dict['pacing'].lower()} pacing, "

        moment_to_moment_detail = prompt_dict.get("moment-to-moment detail", None)
        if moment_to_moment_detail is not None and moment_to_moment_detail.lower() == "high":
            description += f"moment to moment detail, "

        sensory_detail = prompt_dict.get("sensory detail", None)
        if sensory_detail is not None and sensory_detail.lower() != "":
            description += f"{sensory_detail.lower()} detail, "

        description += f"from a {prompt_dict['point of view']} perspective."

        author = prompt_dict.get("author", None)
        if author and author != "N/A":
            description += f" In the style of {author}."

        if tags_line != "":
            style += "\n" + tags_line
        style += "\n" + description
    elif use_key_value:
        def format_prose(k, v):
            if k == "moment-to-moment detail":
                if v.lower() == "high":
                    return "\nIn moment-to-moment detail."
                else:
                    return ""
            elif k == "sensory detail":
                return f"\nIn {v.lower()} detail."
            return f"\nThe {k} is {v.lower()}."

        items = [i for i in prompt_dict.items()]
        random.shuffle(items)
        for key, value in items:
            if not value:
                continue
            if use_key_value:
                if key == "sensory detail":
                    style += f"\ndescriptiveness: {value.lower()}"
                    continue
                if key == "moment-to-moment detail":
                    if prompt_dict[key].lower() != "yes":
                        continue
                style += f"\n{key}: {value.lower()}"
            else:
                style += format_prose(key, value)

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


if __name__ == "__main__":
    pass
