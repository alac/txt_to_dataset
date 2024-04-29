import argparse
import os
import tqdm
import time
import json
import random

from library.batching_utils import get_subpaths_to_process, write_output_and_debug_files
from library.settings_manager import settings, ROOT_FOLDER
from library.prompt_parser import sort_keys, get_full_text_from_prompt_dict, load_prompt_file
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
    if mode == MODE_GENERATE_PROMPT:
        batch_generate_prompts(in_folder, out_folder)
    elif mode == MODE_COUNT_PHRASES:
        batch_count_phrases(in_folder, out_folder)
    elif mode == MODE_RANDOMIZE_NAMES:
        batch_randomize_names(in_folder, out_folder)
    else:
        raise ValueError(f"process_chunk got unexpected mode: {mode}")


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
            continue
        for k, v in new_values.items():
            prompt_dict[k] = v

        directory, filename = os.path.split(subpath)
        result = json.dumps(sort_keys(prompt_dict), indent=4)
        write_output_and_debug_files(os.path.join(out_folder, directory),
                                     filename.replace(".txt", f".json"),
                                     result,
                                     debug_files)


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

    with open("library/names_female.json", "r", encoding='utf-8') as f:
        female_names = json.load(f)
    with open("library/names_male.json", "r", encoding='utf-8') as f:
        male_names = json.load(f)

    replaced_names = {}
    for subpath in tqdm.tqdm(subpaths):
        full_path = os.path.join(in_folder, subpath)
        script_chunk, prompt_dict = load_prompt_file(full_path)

        if not prompt_dict:
            raise ValueError(f"batch_randomize_names: expected prompt files to contain a json: {full_path}")
        for key in ["male characters", "female characters"]:
            if key not in prompt_dict:
                raise ValueError(f"batch_randomize_names: expected prompt json to contain the key {key}: {full_path}")

        prompt_dict, all_replacements = randomize_names(prompt_dict, female_names, male_names)
        for k in all_replacements:
            replaced_names[k] = all_replacements[k]

        directory, filename = os.path.split(subpath)
        result = json.dumps(sort_keys(prompt_dict), indent=4)
        write_output_and_debug_files(os.path.join(out_folder, directory),
                                     filename.replace(".txt", f".json"),
                                     result,
                                     {})

    names_json_path = os.path.join(ROOT_FOLDER, os.path.join(out_folder, "replaced_names.json"))
    with open(names_json_path, 'w', encoding='utf-8') as file:
        file.writelines(json.dumps(replaced_names, indent=4))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        usage="""Batch processing for prompts, applying the chosen process to each file in each subfolder of the input folder.

MODE_GENERATE_PROMPT = Makes an request to an ai model (configurable in settings.toml) and generates a prompt (and metadata) for the file.

MODE_COUNT_PHRASES = Counts 3 repeated word phrases on the subfolder level and globally.
Used to determine whether phrases are over-represented in the dataset.

MODE_RANDOMIZE_NAMES = Uses the name metadata in a prompt file to randomize names in the story.
Useful if the dataset has a bias towards particular names.

python -m process_prompts --input_folder in --output_folder out --keys MODE_GENERATE_PROMPT""")
    parser.add_argument('--input_folder', type=str, required=True,
                        help='Input folder path. Should contain subfolders containing story chunks (.txt) or prompt'
                             ' (.json) files.')
    parser.add_argument('--output_folder', type=str, required=True,
                        help='Output folder path. Will be populated by a mirrored structure as the input folder, with '
                             'modified json files.')
    parser.add_argument('--mode', type=str, required=True,
                        help='Determines what processing to apply: MODE_GENERATE_PROMPT, MODE_COUNT_PHRASES, '
                             'MODE_RANDOMIZE_NAMES.')
    args = parser.parse_args()

    process_prompts(args.input_folder, args.output_folder, args.mode)
