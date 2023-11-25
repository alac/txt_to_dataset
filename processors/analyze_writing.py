import json
import re
import os
from typing import Union

from library.few_shot_request import few_shot_request
from library.settings_manager import settings
from library.ai_requests import EmptyResponseException
from library.token_count import get_token_count
from library.english_constants import indirect_person_words, lazy_contraction_mapping


def generate_prompts(story, blacklist=[], continuation=False, attempts=1, context_length=1000,
                     override_prompt_path=None) -> (Union[None, dict], dict):
    """
    :param story: The text to generate a prompt dictionary for.
    :param blacklist: A set of values that are disallowed from _any_ value in the prompt dictionary.
    :param continuation: If true, splits part of the story into a 'context' that won't be used to generate the prompt.
    :param attempts: The number of times to attempt an AI request to generate a prompt.
    :param context_length: The ideal context length for the output; if attempts > 1, the valid result with the closest
        length will win.
    :param override_prompt_path: The filepath for a few shot prompt to send to the AI. It should have a {story}
        template value.
    :return: A tuple where:
        The first element is None in the case of failure, or the result as a dict[str, str]
        The second element is a dict[str, str], intended to be debug outputs (filename -> content)
    """

    if continuation:
        context_lines = []
        generated_lines = []
        all_lines = story.splitlines(keepends=False)

        def token_count_lines(line_list):
            return sum([get_token_count(l) for l in line_list])

        front, back = 0, len(all_lines) - 1
        for _ in range(len(all_lines)):
            if token_count_lines(generated_lines) <= token_count_lines(context_lines):
                generated_lines.insert(0, all_lines[back])
                back -= 1
            else:
                context_lines.append(all_lines[front])
                front += 1
        context = "\n".join(context_lines)
        story = "\n".join(generated_lines)

    prompt_path = override_prompt_path
    if not prompt_path:
        prompt_path = settings.get_setting('prompt_gen.prompt_file_path')

    junk_outputs = []
    full_outputs = []
    for i in range(attempts):
        try:
            response_dict = few_shot_request(prompt_path,
                                             {"story": story})
        except EmptyResponseException:
            response_dict = {}

        is_junk = False
        result_dict = {}
        if len(response_dict) == 0:
            is_junk = True
        else:
            for key in response_dict:
                result_dict[key.strip().lower()] = response_dict[key]
                if len(response_dict[key]) < 2:  # blank lines and placeholders like "-"
                    is_junk = True
                for banned in blacklist:
                    if banned in response_dict[key]:
                        is_junk = True

        if continuation:
            result_dict["context"] = context.strip()
        result_dict["story"] = story.strip()

        if is_junk or any([k for k in result_dict if result_dict[k] is None]):
            junk_outputs.append(result_dict)
        else:
            full_outputs.append(result_dict)
            break

    best_length = 0
    best_result = None
    for full_output in full_outputs:
        tokens = ""
        for _, v in full_output.items():
            if v:
                tokens += v + " "
        token_count = get_token_count(tokens)
        if abs(context_length - best_length) > abs(context_length - token_count):
            best_length = token_count
            best_result = full_output

    junk_dict = {}
    for i, v in enumerate(junk_outputs):
        junk_dict[f"junk_prompt#{i}"] = json.dumps(v, indent=4)

    return best_result, junk_dict


def count_phrases(story, story_counts, global_counts, count_state,
                  book_mode=False, book_prune_sentences=400, chunk_prune_chunks=20):
    CHUNKS_SINCE_PRUNE = "CHUNKS_SINCE_PRUNE"

    for contraction, unicode_apostrophe in lazy_contraction_mapping.items():
        story = story.replace(contraction, unicode_apostrophe)

    # break the script into chunks that could be phrases
    pattern = r'[.!?;,"()\[\]\u2013\u2014\'"…&]'
    sentences = re.split(pattern, story)
    sentences = [s.strip() for s in sentences if s.strip()]

    def should_skip_phrase(phrase_words: list[str]):
        for w in phrase_words:
            if w.istitle():
                return True
            if w in indirect_person_words:
                return True
        return False

    # process phrases
    phrase_counts = {}
    unpruned = 0
    for sentence in sentences:
        words = sentence.split(" ")
        for length in [3]:
            for i in range(len(words) - length):
                if should_skip_phrase(words[i: i + length]):
                    continue
                phrase = " ".join(words[i: i + length]).replace("’", "'")  # join and undo unicode apostrophe
                phrase_counts[phrase] = 1 + phrase_counts.get(phrase, 0)
        unpruned += 1
        if book_mode and unpruned > book_prune_sentences:
            prune_phrase_counts([phrase_counts], 3)
            unpruned = 0

    if count_state.get(CHUNKS_SINCE_PRUNE, 0) >= chunk_prune_chunks:
        prune_phrase_counts([story_counts, global_counts], 3)
    count_state[CHUNKS_SINCE_PRUNE] = 1 + count_state.get(CHUNKS_SINCE_PRUNE, 0)

    for key in phrase_counts:
        story_counts[key] = phrase_counts[key] + story_counts.get(key, 0)
        global_counts[key] = phrase_counts[key] + global_counts.get(key, 0)

    if book_mode:
        prune_phrase_counts([story_counts, global_counts], 3)


def prune_phrase_counts(dicts, cap):
    for dict in dicts:
        keys = [k for k in dict]
        for key in keys:
            if dict[key] < cap:
                del dict[key]


def finalize_count_phrases(count_state, out_folder=r"user\phrase_counts", min_repeats_in_a_story=5, min_stories_per_phrase=3):
    os.makedirs(out_folder, exist_ok=True)

    global_counts = None
    path_data_pairs = []
    for k in count_state:
        if k == "story_phrases":
            global_counts = count_state[k]
        elif k.startswith("story_phrases"):
            out_path = os.path.join(out_folder, os.path.basename(k) + ".json")
            path_data_pairs.append([out_path, count_state[k]])

    # save the counts for individual stories
    number_of_stories_for_phrase = {}
    for p, d in path_data_pairs:
        prune_phrase_counts([d], min_repeats_in_a_story)
        for phrase in d:
            number_of_stories_for_phrase[phrase] = 1 + number_of_stories_for_phrase.get(phrase, 0)
        sorted_items = sorted(d.items(), key=lambda x: x[1], reverse=True)
        sorted_dict = dict(sorted_items)
        with open(p, 'w') as f:
            json.dump(sorted_dict, f, indent=4)

    # filter global counts, so that phrases must belong to 3 or more stories
    global_counts_with_min_stories = {}
    for phrase in global_counts:
        if number_of_stories_for_phrase.get(phrase, 0) >= min_stories_per_phrase:
            global_counts_with_min_stories[phrase] = global_counts[phrase]
    sorted_items = sorted(global_counts_with_min_stories.items(), key=lambda x: x[1], reverse=True)
    sorted_dict = dict(sorted_items)
    with open(os.path.join(out_folder, "story_phrases.json"), 'w') as f:
        json.dump(sorted_dict, f, indent=4)
