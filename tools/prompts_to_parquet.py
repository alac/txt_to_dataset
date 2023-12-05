import argparse
import os
import tqdm
import pandas as pd

from library.prompt_parser import get_full_text_from_prompt_dict, load_prompt_file


def generate_parquet(in_folder: str, out_file: str):
    input_filepaths = []
    for subfolder in os.listdir(in_folder):
        if not os.path.isdir(os.path.join(in_folder, subfolder)):
            continue
        for filename in os.listdir(os.path.join(in_folder, subfolder)):
            fp = os.path.join(in_folder, subfolder, filename)
            if os.path.isfile(fp) and (fp.endswith(".txt") or fp.endswith(".json")):
                input_filepaths.append(fp)
    input_filepaths = sorted(input_filepaths)

    data_list = []
    for subpath in tqdm.tqdm(input_filepaths):
        script_chunk, prompt_dict = load_prompt_file(os.path.join(subpath))
        story = script_chunk
        if prompt_dict:
            story = get_full_text_from_prompt_dict(prompt_dict)
        data_list.append(story)
    column_names = ['story']
    df = pd.DataFrame(data=data_list, columns=column_names)
    df.to_parquet(out_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        usage="""Generates a parquet file from the "folder of folders of txt/json" structure used everywhere in
txt_to_dataset. Retains only the story data.

python -m tools.prompts_to_parquet --input_folder in --output_file out""")
    parser.add_argument('--input_folder', type=str, required=True,
                        help='Input folder path. Should contain subfolders containing story chunks (.txt) or prompt'
                             ' (.json) files.')
    parser.add_argument('--output_file', type=str, required=True,
                        help='Output path of the parquet file.')
    args = parser.parse_args()

    generate_parquet(args.input_folder, args.output_file)
