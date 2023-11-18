
import os
import tqdm
import time
import json
import random

from library.settings_manager import settings, ROOT_FOLDER
from library.prompt_parser import sort_keys, get_full_text_from_prompt_dict
from processors.analyze_writing import count_phrases, generate_prompts, finalize_count_phrases
from processors.edit_writing import randomize_names

MODE_GENERATE_PROMPT = "MODE_GENERATE_PROMPT"
MODE_COUNT_PHRASES = "MODE_COUNT_PHRASES"
MODE_RANDOMIZE_NAMES = "MODE_RANDOMIZE_NAMES"

KEY_REPLACED_NAMES = f"replaced_names"


def sleep_for_x_hours(duration):
    sleep_duration = duration * 60 * 60  # X hours in seconds
    with tqdm.tqdm(total=sleep_duration, unit='s', desc='Sleeping') as pbar:
        while sleep_duration > 0:
            sleep_amount = min(10, sleep_duration)  # Update the progress bar every 10 seconds
            time.sleep(sleep_amount)
            sleep_duration -= sleep_amount
            pbar.update(sleep_amount)
    print("Finished sleeping.")


def process_prompts(in_folder: str, out_folder: str, mode: str):
    os.makedirs(out_folder, exist_ok=True)
    os.makedirs(os.path.join(out_folder, "extras"), exist_ok=True)

    if mode == MODE_GENERATE_PROMPT:
        batch_generate_prompts(in_folder, out_folder)
    elif mode == MODE_COUNT_PHRASES:
        batch_count_phrases(in_folder, out_folder)
    elif mode == MODE_RANDOMIZE_NAMES:
        batch_randomize_names(in_folder, out_folder)
    else:
        raise ValueError(f"process_chunk got unexpected mode: {mode}")


def get_subpaths_to_process(in_folder: str, out_folder: str) -> list[str]:
    """
    for every file in a subfolder of in_folder, return the subpath relative to in_folder.
    except if a parallel file exists in the out_folder.

    :param in_folder:
    :param out_folder:
    :return:
    """
    subpaths_filenames = []

    for subfolder in os.listdir(in_folder):
        if not os.path.isdir(os.path.join(in_folder, subfolder)):
            continue
        for filename in os.listdir(os.path.join(in_folder, subfolder)):
            out_path = os.path.join(out_folder, subfolder, filename.replace(".txt", ".json"))
            if os.path.isfile(out_path):
                continue
            subpaths_filenames.append(os.path.join(subfolder, filename))
    return subpaths_filenames


def load_prompt_file(filepath: str) -> tuple[str, dict]:
    print("Processing file:", filepath)
    with open(filepath, 'r', encoding='utf-8') as file:
        script_chunk = file.read()
    prompt_dict = None
    try:
        prompt_dict = json.loads(script_chunk)
    except ValueError:  # as a convenience, try to load the script as a dictionary
        pass
    return script_chunk, prompt_dict


def write_outputs(out_folder: str, filename: str, result: str, debug_files: dict[str,str]):
    out_filename = filename.replace(".txt", f".json")
    output_path = os.path.join(out_folder, out_filename)
    if result and len(result):
        with open(output_path, 'w', encoding='utf-8') as file:
            file.writelines(result)
    if debug_files:
        for suffix, contents in debug_files.items():
            if contents:
                output_path = os.path.join(out_folder,
                                           "extras",
                                           out_filename.replace(".json", f"{suffix}.json"))
                with open(output_path, 'w', encoding='utf-8') as file:
                    file.writelines(contents)


def batch_generate_prompts(in_folder: str, out_folder: str):
    subpaths = get_subpaths_to_process(in_folder, out_folder)

    for subpath in tqdm.tqdm(subpaths):
        script_chunk, prompt_dict = load_prompt_file(os.path.join(in_folder, subpath))
        story = script_chunk
        if prompt_dict:
            story = get_full_text_from_prompt_dict(prompt_dict)
        else:
            prompt_dict = {}

        continuation = (random.random() < settings.get_setting("prompt_gen.continuation_likelyhood"))
        if "story" in prompt_dict:
            # if we're redoing part of a prompt, we want to preserve the existing split between context/story
            continuation = False
            story = prompt_dict["story"]

        new_values, debug_files = generate_prompts(story, attempts=3, continuation=continuation)
        if new_values is None or len(new_values) == 0:
            print(f"No data from AI request; skipping {os.path.join(in_folder, subpath)}")
            return
        for k, v in new_values.items():
            prompt_dict[k] = v

        result = json.dumps(sort_keys(prompt_dict), indent=4)

        directory, filename = os.path.split(subpath)
        write_outputs(os.path.join(out_folder, directory), filename, result, debug_files)


def batch_count_phrases(in_folder: str, out_folder: str):
    subpaths = get_subpaths_to_process(in_folder, out_folder)

    count_dict = {}
    for subpath in tqdm.tqdm(subpaths):
        script_chunk, prompt_dict = load_prompt_file(os.path.join(in_folder, subpath))
        story = script_chunk
        if prompt_dict:
            story = get_full_text_from_prompt_dict(prompt_dict)
        story_count_key = f"story_phrases_{in_folder}"
        global_count_key = f"story_phrases"
        count_dict[story_count_key] = count_dict.get(story_count_key, {})
        count_dict[global_count_key] = count_dict.get(global_count_key, {})
        count_phrases(story, count_dict[story_count_key], count_dict[global_count_key], count_dict,
                      book_prune_sentences=12000, chunk_prune_chunks=800)

    finalize_count_phrases(count_dict)


def batch_randomize_names(in_folder: str, out_folder: str):
    subpaths = get_subpaths_to_process(in_folder, out_folder)

    replaced_names = {}
    for subpath in tqdm.tqdm(subpaths):
        script_chunk, prompt_dict = load_prompt_file(os.path.join(in_folder, subpath))

        if not prompt_dict:
            raise ValueError("batch_randomize_names: expected prompt files to contain a json.")
        for key in ["male characters", "female characters"]:
            if key not in prompt_dict:
                raise ValueError(f"batch_randomize_names: expected prompt json to contain the key {key}.")

        prompt_dict, all_replacements = randomize_names(prompt_dict)
        for k in all_replacements:
            replaced_names[k] = all_replacements[k]
        result = json.dumps(sort_keys(prompt_dict), indent=4)

        directory, filename = os.path.split(subpath)
        write_outputs(os.path.join(out_folder, directory), filename, result, {})

    names_json_path = os.path.join(ROOT_FOLDER, os.path.join(out_folder, "replaced_names.json"))
    with open(names_json_path, 'w', encoding='utf-8') as file:
        file.writelines(json.dumps(replaced_names, indent=4))
