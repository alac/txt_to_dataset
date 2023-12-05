import os
import json
import tqdm
import argparse

from library.ai_requests import run_ai_request


def run(filepath: str, out_folder: str, trials: int, response_length: int):
    assert os.path.exists(filepath)
    replacements_path = filepath.replace(".txt", ".replacements.json")
    assert os.path.exists(replacements_path)
    os.makedirs(out_folder, exist_ok=True)

    with open(replacements_path, 'r', encoding='utf-8') as file:
        replacements_json = json.loads(file.read())

    with open(filepath, 'r', encoding='utf-8') as file:
        template = file.read()

    for prompt, out_file in tqdm.tqdm(get_prompt_and_outfile(template, replacements_json, out_folder, trials)):
        if os.path.exists(out_file):
            continue
        result = run_ai_request(prompt, ["### System:", "### User:", "### Assistant:"], temperature=.8,
                                ban_eos_token=True, max_response=response_length)
        with open(out_file, 'w', encoding="utf-8") as f:
            f.write(prompt)
            f.write("\n")
            f.write(result)


def get_prompt_and_outfile(template, replacements_json, out_folder, trials):
    for index, replacements in enumerate(iterate_over_all_possible_dictionaries(replacements_json)):
        prompt = template.format_map(replacements)
        chosen_indices = ""
        for key in replacements_json:
            chosen_indices += key + str(replacements_json[key].index(replacements[key])) + "_"

        for trial in range(trials):
            out_file = os.path.join(out_folder, f"{chosen_indices}_trial{trial}.txt")
            yield prompt, out_file


def iterate_over_all_possible_dictionaries(dictionary):
    if not dictionary:
        yield {}
        return

    key, values = next(iter(dictionary.items()))
    for value in values:
        for sub_dictionary in iterate_over_all_possible_dictionaries({
            k: v for k, v in dictionary.items() if k != key
        }):
            yield {key: value, **sub_dictionary}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        usage="""Batch generate responses from an AI and write the results to a folder.
Uses an input template and a json specifying template values to generate requests.

python -m tools.prompt_tester --prompt_template tools/prompt_test_templates/story_template.txt
    --output_folder out --trials 1 --response_length 600""")
    parser.add_argument('--prompt_template', type=str, required=True, help='The base template filename. Each template '
                        'is assumed to have a json that specifies the template values.')
    parser.add_argument('--output_folder', type=str, required=True, help='Output folder path. Will be populated by '
                        'the results of the AI requests.')
    parser.add_argument('--trials', type=int, required=True, help='The number of attempts per template combination.')
    parser.add_argument('--response_length', type=int, required=True, help='The max number of tokens to generate '
                        'in each response.')
    args = parser.parse_args()

    run(args.prompt_template, args.output_folder, args.trials, args.response_length)
