import random


authors_dist = {
}


def narrow_authors_in_prompt_dict(prompt_dict: dict, min_samples: int = 20) -> dict:
    """
    Hypothesis:
    - too many values for tags makes them less useful (e.g. "author: a, b" vs "author: a").
    - too few examples for a given tag probably does as well.
    What are we doing about it?
    - if an author doesn't have enough datapoints, drop it from tag values, even if that would result in N/A.
    - when there are two authors and both have 'enough' datapoints, pick one randomly (weighted to favor the less
    popular one).
    :param prompt_dict:
    :param min_samples: number of examples for the author to be used.
    :return:
    """
    if len(authors_dist) == 0:
        return prompt_dict

    if prompt_dict.get("author", None) not in [None, ""]:
        return prompt_dict

    similar_authors = prompt_dict.get("similar writers", None)
    if similar_authors in [None, "N/A"]:
        return prompt_dict

    candidate_authors = [c.strip() for c in similar_authors.split(",") if c.lower().strip() in authors_dist]
    candidate_authors = [c for c in candidate_authors if authors_dist[c.lower()] > min_samples and c != "N/A"]

    if len(candidate_authors) > 1:
        total = sum([authors_dist[c.lower()] for c in candidate_authors])
        choice = random.choices(
            candidate_authors,
            [(total - authors_dist[c.lower()])/total for c in candidate_authors]
        )
        candidate_authors = choice

    if len(candidate_authors) == 0:
        candidate_authors = ["N/A"]
    prompt_dict["similar writers"] = candidate_authors[0]
    prompt_dict["author"] = candidate_authors[0]
    return prompt_dict


similar_keys = {
    "writing style": {
        "character-focused": "character-driven",
        "with a focus on characterization": "character-driven",
        "with a focus on character development": "character-driven",
        "characterization": "character-driven",

        "with a focus on character interactions": "character interactions",

        "with vivid imagery": "vivid",
        "vivid imagery": "vivid",

        "dialogue-driven": "dialogue-heavy",
        "dialogue": "dialogue-heavy",
        "with a focus on dialogue": "dialogue-heavy",

        "emotional depth": "emotional",
        "emotions": "emotional",
        "emotive": "emotional",
        "with a focus on the characters’ emotions": "emotional",

        "metaphors": "metaphorical",

        "ornate": "flowery",

        "with a touch of humor": "humorous",
    },
    "tone": {
        "reflective": "melancholic",
        "melancholy": "melancholic",
        "introspective": "melancholic",
        "contemplative": "melancholic",

        "wistful": "nostalgic",

        "despair": "hopeless",

        "playful": "whimsical",

        "with moments of humor": "humorous",
        "with moments of dark humor": "dark humor",
        "with a touch of irony": "ironic",

        "absurdity": "absurd",

        "urgent": "intense",
        "one of tension": "tense",
        "with moments of tension": "tense",
        "with a sense of danger": "thrilling",
        "with a sense of impending danger": "thrilling",
        "fearful": "thrilling",
    },
    "style of humor": {
        "irony": "ironic",
        "satire": "satirical",
        "witty banter": "witty",
        "wit": "witty",
        "dark": "dark humor",
        "dark comedy": "dark humor",
        "sarcastic": "sarcasm",
    },
    "sensory detail": {
        "low": "abstract",
        "medium": "selective",
        "high": "vivid sensory",
    }
}


def alias_similar_keys(prompt_dict: dict) -> dict:
    """
    Hypothesis:
    - without a huge dataset, it's better to have one keyword per concept (e.g. instead of 'satire' and 'satirical'
    both being tags, we'd be better off with just one of them).
    :param prompt_dict:
    :param min_samples: number of examples for the author to be used.
    :return:
    """
    for key in similar_keys:
        val = prompt_dict.get(key, None)
        if val in ["", None]:
            continue
        val = val.lower().strip(".")
        remapping = similar_keys[key]
        if val in remapping:
            prompt_dict[key] = remapping[val]
            continue
        elif "," in val:
            if " and " in val:
                val = val.replace(" and ", ", and ").replace(",,", ",")
            if "with a touch of " in val:
                val = val.replace("with a touch of ", "")
            parts = [p.strip() for p in val.split(",")]
            if parts[-1].startswith("and "):
                parts[-1] = parts[-1][4:]
            parts = [remapping.get(p, p) for p in parts]
            prompt_dict[key] = ", ".join(set(parts))
    return prompt_dict


def prompt_dict_to_style_string(prompt_dict: dict) -> dict:
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
        description += f"in moment to moment detail, "

    sensory_detail = prompt_dict.get("sensory detail", None)
    if sensory_detail not in ["", None]:
        description += f"in {sensory_detail.lower()} detail, "

    point_of_view = prompt_dict.get("point of view", None)
    if point_of_view not in ["", None]:
        description += f"from a {point_of_view} perspective."

    if description.endswith(", "):
        description = description[:-2] + "."

    author = prompt_dict.get("author", None)
    if author and author != "N/A":
        description += f" In the style of {author}."

    style = ""
    if tags_line != "":
        style += "\n" + tags_line
    style += "\n" + description
    return style


def undo_hyphens(prompt):
    if "Write a scene where\n-" in prompt:
        prompt = prompt.replace("Write a scene where\n-", "Write a scene where: ")
        return prompt.replace("\n-", " ").replace("  ", " ")
    return prompt


if __name__ == "__main__":
    print(alias_similar_keys({"style of humor": "irony, satirical, dark and wit"}))
    print(alias_similar_keys({"style of humor": "irony, satirical, dark, and wit"}))
    print(alias_similar_keys({"style of humor": "irony, satirical, dark,and wit"}))
    print(alias_similar_keys({"style of humor": "irony, satirical, dark, wit"}))
