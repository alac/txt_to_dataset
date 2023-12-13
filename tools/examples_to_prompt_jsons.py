import argparse
import os
import tqdm
import json

from library.prompt_parser import sort_keys, load_prompt_file


def get_subpaths_to_process(in_folder: str, out_folder: str) -> list[str]:
    """
    for every file in in_folder, return the subpath relative to in_folder.
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
    return sorted(subpaths_filenames)


def write_outputs(out_folder: str, filename: str, result: str, debug_files: dict[str,str]):
    os.makedirs(out_folder, exist_ok=True)

    out_filename = filename.replace(".txt", f".json")
    output_path = os.path.join(out_folder, out_filename)
    if result and len(result):
        with open(output_path, 'w', encoding='utf-8') as file:
            file.writelines(result)
    if debug_files:
        for suffix, contents in debug_files.items():
            if contents:
                os.makedirs(os.path.join(out_folder, "extras"), exist_ok=True)
                output_path = os.path.join(out_folder,
                                           "extras",
                                           out_filename.replace(".json", f"{suffix}.json"))
                with open(output_path, 'w', encoding='utf-8') as file:
                    file.writelines(contents)


def convert_examples(in_folder: str, out_folder: str):
    subpaths = get_subpaths_to_process(in_folder, out_folder)

    for subpath in tqdm.tqdm(subpaths):
        raw_text, _ = load_prompt_file(os.path.join(in_folder, subpath))
        prompt_dict = {}

        assert "\n\n\n\n\n" in raw_text, f"splitter not found in {subpath}"

        input, response = raw_text.split("\n\n\n\n\n", maxsplit=1)
        prompt_dict["prompt"] = input.strip()
        prompt_dict["story"] = response.strip()

        directory, filename = os.path.split(subpath)
        result = json.dumps(sort_keys(prompt_dict), indent=4)
        write_outputs(os.path.join(out_folder, directory), filename, result, {})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        usage="""Batch processing for prompts, applying the chosen process to each file in each subfolder of the input folder.
Takes an input text file and turns it into a prompt json file.
Assumes only two fields 'prompt' and 'story' (e.g. USER and ASSISTANT) split by five consecutive newlines.

python -m tools.examples_to_prompt_jsons --input_folder in --output_folder out""")
    parser.add_argument('--input_folder', type=str, required=True,
                        help='Input folder path. Should contain subfolders containing story chunks (.txt) or prompt'
                             ' (.json) files.')
    parser.add_argument('--output_folder', type=str, required=True,
                        help='Output folder path. Will be populated by a mirrored structure as the input folder, with '
                             'modified json files.')
    args = parser.parse_args()

    convert_examples(args.input_folder, args.output_folder)
