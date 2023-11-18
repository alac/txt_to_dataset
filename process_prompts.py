
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
MODE_ANALYZE_PACING_DETAIL = "MODE_ANALYZE_PACING_DETAIL"
MODE_ANALYZE_HUMOR = "MODE_HUMOR"
MODE_ANALYZE_HUMOR_REVISE = "MODE_HUMOR_REVISE"
MODE_COUNT_PHRASES = "MODE_COUNT_PHRASES"
MODE_RANDOMIZE_NAMES = "MODE_RANDOMIZE_NAMES"

KEY_REPLACED_NAMES = f"replaced_names"


def process_folder_chunk_pass(in_folder, out_folder, mode, misc={}, queue=None):
    """
    take a folder of files, apply a THING to them, and dump them to the out folder

    :param in_folder:
    :param out_folder:
    :return:
    """
    for filename in tqdm.tqdm(os.listdir(in_folder)):
        if os.path.isfile(os.path.join(in_folder, filename)):
            output_filename = filename
            output_path = os.path.join(out_folder, output_filename)
            if not os.path.exists(output_path) and filename.endswith(".json"):
                cmd = lambda a=in_folder, b=filename, c=out_folder, d=mode, e=misc: \
                    process_chunk(a, b, c, d, misc=e)
                if queue is not None:
                    queue.append(cmd)
                else:
                    cmd()
    return queue


def process_chunk(in_folder, filename, out_folder, mode, misc={}):
    os.makedirs(out_folder, exist_ok=True)
    os.makedirs(os.path.join(out_folder, "extras"), exist_ok=True)

    fp = os.path.join(in_folder, filename)
    print("Processing file:", fp)
    with open(fp, 'r', encoding='utf-8') as file:
        script_chunk = file.read()

    prompt_dict = None
    try:
        prompt_dict = json.loads(script_chunk)
    except ValueError:  # as a convenience, try to load the script as a dictionary
        pass

    result = None  # a string to be written to out_folder/filename
    debug_files = {}  # extra files to be written to out_folder/extras/filename[suffix]; {"suffix": file_contents}
    if mode == MODE_GENERATE_PROMPT:
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
            print(f"No data from AI request; skipping {fp}")
            return
        for k, v in new_values.items():
            prompt_dict[k] = v

        result = json.dumps(sort_keys(prompt_dict), indent=4)
    elif mode == MODE_COUNT_PHRASES:
        story = script_chunk
        if prompt_dict:
            story = get_full_text_from_prompt_dict(prompt_dict)
        story_count_key = f"story_phrases_{in_folder}"
        global_count_key = f"story_phrases"
        misc[story_count_key] = misc.get(story_count_key, {})
        misc[global_count_key] = misc.get(global_count_key, {})
        count_phrases(story, misc[story_count_key], misc[global_count_key], misc,
                      book_prune_sentences=12000, chunk_prune_chunks=800)
    elif mode == MODE_RANDOMIZE_NAMES:
        prompt_dict, all_replacements = randomize_names(prompt_dict)
        misc[KEY_REPLACED_NAMES] = misc.get(KEY_REPLACED_NAMES, {})
        for k in all_replacements:
            misc[KEY_REPLACED_NAMES][k] = all_replacements[k]
        result = json.dumps(sort_keys(prompt_dict), indent=4)
    else:
        raise ValueError(f"process_chunk got unexpected mode: {mode}")

    out_filename = filename.replace(".txt", f".json")
    output_path = os.path.join(out_folder, out_filename)
    if result and len(result):
        with open(output_path, 'w', encoding='utf-8') as file:
            file.writelines(result)
    if debug_files:
        for suffix, contents in debug_files.items():
            if contents:
                output_path = os.path.join(out_folder, "extras", out_filename.replace(".json", f"{suffix}.json"))
                with open(output_path, 'w', encoding='utf-8') as file:
                    file.writelines(contents)


def finalize_processing(mode, misc={}):
    if mode == MODE_COUNT_PHRASES:
        finalize_count_phrases(misc)
    elif mode == MODE_RANDOMIZE_NAMES:
        replaced_names = misc[KEY_REPLACED_NAMES]
        with open(os.path.join(ROOT_FOLDER, "user\\replaced_names.json"), 'w', encoding='utf-8') as file:
            file.writelines(json.dumps(replaced_names, indent=4))


def sleep_for_x_hours(duration):
    sleep_duration = duration * 60 * 60  # X hours in seconds
    with tqdm.tqdm(total=sleep_duration, unit='s', desc='Sleeping') as pbar:
        while sleep_duration > 0:
            sleep_amount = min(10, sleep_duration)  # Update the progress bar every 10 seconds
            time.sleep(sleep_amount)
            sleep_duration -= sleep_amount
            pbar.update(sleep_amount)
    print("Finished sleeping.")
