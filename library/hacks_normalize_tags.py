import random


authors_dist = {
    "ursula k. le guin": 586,
    "george r.r. martin": 432,
    "patrick rothfuss": 381,
    "charles dickens": 331,
    "octavia butler": 280,
    "gene wolfe": 236,
    "thomas pynchon": 228,
    "neil gaiman": 225,
    "china mi\u00e9ville": 225,
    "miguel de cervantes": 217,
    "david foster wallace": 156,
    "f. scott fitzgerald": 147,
    "china mieville": 138,
    "kurt vonnegut": 135,
    "herman melville": 130,
    "joseph heller": 128,
    "vladimir nabokov": 128,
    "terry pratchett": 118,
    "neal stephenson": 108,
    "chuck palahniuk": 103,
    "alastair reynolds": 94,
    "jack london": 90,
    "jonathan swift": 83,
    "oscar wilde": 83,
    "bret easton ellis": 81,
    "cormac mccarthy": 78,
    "robert harris": 76,
    "ernest hemingway": 73,
    "william gibson": 71,
    "marquis de sade": 66,
    "douglas adams": 57,
    "haruki murakami": 56,
    "orson scott card": 53,
    "arthur c. clarke": 52,
    "jane austen": 49,
    "georges bataille": 46,
    "gabriel garcia marquez": 46,
    "robert e. howard": 44,
    "philip k. dick": 43,
    "homer": 43,
    "james joyce": 43,
    "lewis carroll": 42,
    "william faulkner": 42,
    "edgar allan poe": 41,
    "robert a. heinlein": 40,
    "j.k. rowling": 38,
    "louisa may alcott": 38,
    "ana\u00efs nin": 37,
    "bernard cornwell": 37,
    "robert jordan": 36,
    "hilary mantel": 36,
    "lois mcmaster bujold": 34,
    "el james": 31,
    "robin hobb": 31,
    "henry miller": 30,
    "david sedaris": 28,
    "anais nin": 28,
    "james oliver curwood": 28,
    "iain m. banks": 28,
    "fyodor dostoevsky": 27,
    "flannery o'connor": 26,
    "gillian flynn": 25,
    "joe abercrombie": 25,
    "h.p. lovecraft": 25,
    "joseph conrad": 25,
    "charles bukowski": 24,
    "margaret atwood": 23,
    "sylvia day": 22,
    "don delillo": 22,
    "alex": 21,
    "j.r.r. tolkien": 21,
    "gary paulsen": 21,
    "virginia woolf": 21,
    "nathaniel hawthorne": 21,
    "robert louis stevenson": 20,
    "laurence sterne": 18,
    "banana yoshimoto": 18,
    "hunter s. thompson": 17,
    "er pope": 17,
    "ann leckie": 17,
    "j.d. salinger": 16,
    "franz kafka": 16,
    "voltaire": 15,
    "george orwell": 15,
    "erica jong": 14,
    "patrick o'brian": 14,
    "robert graves": 14,
    "william s. burroughs": 13,
    "albert camus": 13,
    "frank herbert": 13,
    "ben kane": 13,
    "ray bradbury": 12,
    "charlotte bronte": 12,
    "anne rice": 12,
    "isaac asimov": 12,
    "willa cather": 12,
    "rudyard kipling": 12,
    "victor hugo": 12,
    "jeff v": 12,
    "ermeer": 12,
    "zane grey": 11,
    "laura ingalls wilder": 11,
    "paula hawkins": 11,
    "h.g. wells": 10,
    "louis l'amour": 10,
    "elmore leonard": 9,
    "augusten burroughs": 9,
    "toni morrison": 9,
    "p.g. wodehouse": 8,
    "stephen king": 7,
    "n/a": 7,
    "evelyn waugh": 7,
    "tracy chevalier": 7,
    "henry fielding": 6,
    "milan kundera": 6,
    "samuel beckett": 6,
    "dennis lehane": 5,
    "none provided": 5,
    "robert asprin": 5,
    "neal asher": 5,
    "nora roberts": 5,
    "edith wharton": 5,
    "l. frank baum": 5,
    "larry mcmurtry": 5,
    "re dumas": 4,
    "daniel defoe": 4,
    "saul bellow": 4,
    "philip roth": 4,
    "sarah vowell": 4,
    "isabel allende": 4,
    "james clavell": 4,
    "nicholas sparks": 4,
    "patricia highsmith": 4,
    "donna tartt": 4,
    "denis johnson": 4,
    "thomas hardy": 4,
    "j.g. ballard": 4
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


if __name__ == "__main__":
    print(alias_similar_keys({"style of humor": "irony, satirical, dark and wit"}))
    print(alias_similar_keys({"style of humor": "irony, satirical, dark, and wit"}))
    print(alias_similar_keys({"style of humor": "irony, satirical, dark,and wit"}))
    print(alias_similar_keys({"style of humor": "irony, satirical, dark, wit"}))
