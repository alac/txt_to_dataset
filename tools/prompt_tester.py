import os
import json
import tqdm

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
        result = run_ai_request(prompt, "", ["### System:", "### User:", "### Assistant:"], temperature=.8,
                                ban_eos_token=True, max_response=response_length, print_progress=False)
        with open(out_file, 'w') as f:
            f.write(prompt)
            f.write("\n")
            f.write(result)


def get_prompt_and_outfile(template, replacements_json, out_folder, trials):
    for index, replacements in enumerate(iterate_over_all_possible_dictionaries(replacements_json)):
        prompt = template.format_map(replacements)
        indices = ""
        for key in replacements_json:
            indices += str(replacements_json[key].index(replacements[key])) + "_"

        for trial in range(trials):
            out_file = os.path.join(out_folder, f"{indices}_{trial}.txt")
            yield (prompt, out_file)


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
    run(r"tools/prompt_test_templates/story_template.txt", r"user/quality_tests/ww21", 1, 600)
