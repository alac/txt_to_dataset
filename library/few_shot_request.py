import json
import os

from library.ai_requests import run_ai_request, EmptyResponseException
from library.token_count import get_token_count


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
                            custom_stopping_strings=settings_json.get("stopping_strings", ["\n\n"]),
                            temperature=settings_json.get("temperature", .2),
                            max_response=settings_json.get("response_length", 600),
                            ban_eos_token=True)
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
    all_examples = [d for d in all_examples if d]
    return all_examples
