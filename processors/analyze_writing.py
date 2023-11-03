import json
import re
import os

from library.settings_manager import settings
from library.ai_requests import run_ai_request, EmptyResponseException
from library.token_count import get_token_count
from library.english_constants import indirect_person_words, lazy_contraction_mapping


def generate_prompts(story, blacklist=[], continuation=False, attempts=3, context_length=1950,
                     override_prompt_path=None):
    if continuation:
        # break the text we want to generate a prompt for into a 'context' and the 'text'
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
        # print(json.dumps(response_dict, indent=2))

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

    return {}, {}


def prune_phrase_counts(dicts, cap):
    for dict in dicts:
        keys = [k for k in dict]
        for key in keys:
            if dict[key] < cap:
                del dict[key]


def finalize_count_phrases(count_state, out_folder="user\phrase_counts", min_repeats_in_a_story=5, min_stories_per_phrase=3):
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


def few_shot_request(template_filepath: str, replacements: dict) -> dict:
    """
We're expecting the template file to be of a format like this:
    >name: John
    >age: 23
    >biography: paragraph1
    paragraph2
    paragraph3
    >shoe size: 20

    >name: Bill
So, the format is:
- all keys are preceded by ">" and followed by ": ".
- lines without a key are assumed to belong to the previous key.
- we rely on dummy '>key:value' lines to terminate multiline elements.
- a blank line signifies the end of one entry.
- the final entry is expected to be filled out by the AI, we should make sure not to mess it up with excess spacing.
    """
    assert os.path.exists(template_filepath)
    with open(template_filepath, 'r', encoding='utf-8') as file:
        template = file.read()

    template_settings = template_filepath.replace(".txt", ".params.json")
    assert os.path.exists(template_settings)
    with open(template_settings, 'r', encoding='utf-8') as file:
        settings_json = json.loads(file.read())

    request = template.format_map(replacements)
    remove_keys = settings_json.get("remove_keys_from_prompt", [])
    if remove_keys:
        request = edit_few_shot_request(request, remove_keys)

    print("running request of size, ", get_token_count(request))
    result = run_ai_request(request,
                            "",
                            settings_json.get("stopping_strings", ["\n\n"]),
                            temperature=settings_json.get("temperature", .2),
                            ban_eos_token=True,
                            max_response=settings_json.get("response_length", 600),
                            print_progress=False)
    if len(result) == 0:
        raise EmptyResponseException("AI request returned an empty response. Is the connection to the AI working?")

    if result.endswith("\n>"):
        result = result[:-2]

    result_dict = parse_few_shot_format(result)[0]
    remove_keys = settings_json.get("remove_keys_from_result", [])
    for remove_key in remove_keys:
        del result_dict[remove_key]

    return result_dict


def edit_few_shot_request(prompt: str, remove_keys: list[str]) -> str:
    all_examples = parse_few_shot_format(prompt)
    result_lines = []
    for index, example in enumerate(all_examples):
        for key in example:
            if key in remove_keys:
                continue
            result_lines.append(f">{key}: " + example[key])
        if index != len(all_examples) - 1:
            result_lines.append("")  # the join will turn this into a blank line

    return "\n".join(result_lines)


def parse_few_shot_format(prompt) -> list[dict]:
    example = {}
    all_examples = [example]
    last_key = None
    for line in prompt.splitlines():
        if len(line.strip()) == 0:
            if len(example.keys()):
                example = {}
                all_examples.append(example)
                last_key = None
        elif line.startswith(">") and ":" in line:
            line = line[1:]
            key, value = line.split(":", 1)
            last_key = key.strip()
            if value.startswith(" "):
                value = value[1:]
            example[last_key] = value
        elif last_key is not None:
            example[last_key] += "\n" + line
    return all_examples
