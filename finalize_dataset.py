import os
import json
import random

import tqdm

from library.prompt_parser import generate_dataset_row_from_prompt_dict, prepare_prompt_dict_for_row,\
    estimate_total_tokens
from library.settings_manager import settings
from library.hacks_dataset_specific import narrow_authors_in_prompt_dict, alias_similar_keys

PROMPT_CACHE = {}


def track_prompt_metrics(prompt_dict, info_dict):
    """
    Track distribution of fields across prompt_dicts and save to the info_dict
    :param prompt_dict:
    :param info_dict:
    :return:
    """
    def preprocess_field(field: str, field_value: str):
        if field_value.endswith("."):
            field_value = field_value[:-1]
        values_list = [field_value]
        if "," in field_value:
            values_list = field_value.split(",")
        if any([("and" in f) for f in values_list]):
            new_list = []
            [new_list.extend([nf.strip() for nf in nl.split("and")]) for nl in values_list]
            values_list = new_list
        if field == 'point of view':
            if "(" in field_value:
                # take "Third Person" from "Third Person (blah)"
                values_list = [field_value[:field_value.index("(")]]
            else:
                values_list = [field_value]
        values_list = [v.strip().lower() for v in values_list]
        return values_list

    for key, value in prompt_dict.items():
        if key in ["prompt", "context", "story", "humorous elements"]:
            continue
        if value:
            values_split = preprocess_field(key, value)
            for split_value in values_split:
                info_dict[key] = info_dict.get(key, {})
                info_dict[key][split_value] = info_dict[key].get(split_value, 0) + 1


def make_dataset(prompts_folders, outfile_path, validation_path, info_path, max_tokens=None, min_tokens=None):
    all_prompts = []
    info_dict = {}
    queue = []
    for prompts_folder in prompts_folders:
        for story_name in os.listdir(prompts_folder):
            if not os.path.isdir(os.path.join(prompts_folder, story_name)):
                continue
            for prompt_file in os.listdir(os.path.join(prompts_folder, story_name)):
                prompt_fp = os.path.join(prompts_folder, story_name, prompt_file)
                if os.path.isfile(prompt_fp) and prompt_file.endswith(".txt"):
                    queue.append(prompt_fp)

    for prompt_fp in tqdm.tqdm(queue):
        try:
            if prompt_fp in PROMPT_CACHE:
                new_prompt, tokens_used, prompt_dict, length = PROMPT_CACHE[prompt_fp]
            else:
                with open(prompt_fp, 'r') as file:
                    prompt_json = file.read()
                prompt_dict = json.loads(prompt_json)
                prompt_dict = prepare_prompt_dict_for_row(prompt_dict)
                if settings.get_setting("hacks.redistribute_authors"):
                    prompt_dict = narrow_authors_in_prompt_dict(prompt_dict)
                if settings.get_setting("hacks.swap_values"):
                    prompt_dict = alias_similar_keys(prompt_dict)
                try:
                    prompt_dict, style, context, inst, length, story, system = generate_dataset_row_from_prompt_dict(
                        prompt_dict,
                        droppable_tags=settings.get_setting("prompt_format.droppable_tags"),
                        drop_tags_prob=settings.get_setting("prompt_format.tag_drop_rate"))
                    tokens_used = estimate_total_tokens([style, context, inst, story, system])
                except Exception as e:
                    print("Exception on:", prompt_dict)
                    raise e

                new_prompt = {'system': system,
                              'context': context,
                              'instruction': (style + "\n" + inst).strip(),
                              'output': story}
                if context is None:
                    del new_prompt['context']
                PROMPT_CACHE[prompt_fp] = (new_prompt, tokens_used, prompt_dict, length)

            if max_tokens is not None:
                if tokens_used > max_tokens:
                    continue
            if min_tokens is not None:
                if tokens_used < min_tokens:
                    continue

            track_prompt_metrics(prompt_dict, info_dict)
            track_prompt_metrics({"length": length}, info_dict)

            all_prompts.append(new_prompt)

        except Exception as e:
            print("Exception while processing: ", prompt_fp)
            raise e

    validation_set, dataset = random_split(all_prompts, settings.get_setting("prompt_format.validation_set_size"))
    with open(outfile_path, 'w') as outfile:
        for p in dataset:
            outfile.write(json.dumps(p) + "\n")
    if validation_set:
        with open(validation_path, 'w') as outfile:
            for p in validation_set:
                outfile.write(json.dumps(p) + "\n")

    final_metrics_dict = {}
    # sort and filter out fields values with less than 10 results
    for field, distribution in info_dict.items():
        sorted_items = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
        sorted_dict = dict([i for i in sorted_items if i[1] > 10])
        final_metrics_dict[field] = sorted_dict
    with open(info_path, 'w') as outfile:
        json.dump(final_metrics_dict, outfile, indent=2)


def random_split(array, split_ratio):
    n = len(array)
    split_index = int(split_ratio * n)
    random.shuffle(array)  # Shuffle the array randomly
    subarray_1 = array[:split_index]
    subarray_2 = array[split_index:]
    return subarray_1, subarray_2


def generate_datasets(input_folders, output_folder, write_all_combinations=True, max_tokens=None, min_tokens=None):
    name_to_folder = {}
    for in_folder in input_folders:
        name = os.path.basename(in_folder.strip(os.path.sep))
        name_to_folder[name] = in_folder

    subsets = [[k for k in name_to_folder]]
    if write_all_combinations:
        subsets = [[]]
        for name in name_to_folder:
            for i in range(len(subsets)):
                new_set = subsets[i].copy()
                new_set.append(name)
                subsets.append(new_set)

    for subset in subsets:
        if len(subset) == 0:
            continue
        folders = sorted([name_to_folder[s] for s in subset])
        print("generating subset: ", subset)
        output_file = os.path.join(output_folder, "dataset_" + "_".join(subset))
        if max_tokens is not None:
            output_file += f"MAX{max_tokens}"
        if min_tokens is not None:
            output_file += f"MIN{min_tokens}"
        make_dataset(
            folders,
            output_file + ".json",
            output_file + "_val.json",
            output_file + "_info.json",
            max_tokens=max_tokens,
            min_tokens=min_tokens
        )
