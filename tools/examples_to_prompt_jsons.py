import argparse
import os
import tqdm
import json

from library.batching_utils import get_subpaths_to_process, write_output_and_debug_files
from library.prompt_parser import sort_keys, load_prompt_file


def convert_examples(in_folder: str, out_folder: str):
    subpaths = get_subpaths_to_process(in_folder, out_folder)

    for subpath in tqdm.tqdm(subpaths):
        raw_text, _ = load_prompt_file(os.path.join(in_folder, subpath))
        prompt_dict = {}

        assert "\n\n---\n\n" in raw_text, f"splitter not found in {subpath}"

        parts = raw_text.split("\n\n---\n\n", maxsplit=3)

        if len(parts) == 3:
            prompt_dict["context"], prompt_dict["prompt"], prompt_dict["story"] = parts
        elif len(parts) == 2:
            prompt_dict["prompt"], prompt_dict["story"] = parts

        directory, filename = os.path.split(subpath)
        result = json.dumps(sort_keys(prompt_dict), indent=4)
        write_output_and_debug_files(os.path.join(out_folder, directory),
                                     filename.replace(".txt", f".json"),
                                     result,
                                     {})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        usage="""Batch processing for prompts, applying the chosen process to each file in each subfolder of the input folder.
Takes an input text file and turns it into a prompt json file.
Assumes only two fields 'prompt' and 'story' (e.g. USER and ASSISTANT) split by "---" surrounded by two blank lines.

python -m tools.examples_to_prompt_jsons --input_folder in --output_folder out""")
    parser.add_argument('--input_folder', type=str, required=True,
                        help='Input folder path. Should contain subfolders containing story chunks (.txt) or prompt'
                             ' (.json) files.')
    parser.add_argument('--output_folder', type=str, required=True,
                        help='Output folder path. Will be populated by a mirrored structure as the input folder, with '
                             'modified json files.')
    args = parser.parse_args()

    convert_examples(args.input_folder, args.output_folder)
