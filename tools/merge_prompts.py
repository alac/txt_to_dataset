""" merge_prompts takes in two folders with the /group/story/chunk.json structure and merged prompts from the
first folder with specific key/value pairs of prompts from the second folder. """

import os
import tqdm
import json
import argparse

from library.prompt_parser import sort_keys


def process_folder_chunk_pass(merge_base_folder, merge_extract_folder, merge_keys, out_folder, queue=None):
    for filename in tqdm.tqdm(os.listdir(merge_base_folder)):
        if os.path.isfile(os.path.join(merge_base_folder, filename)):
            output_filename = filename
            output_path = os.path.join(out_folder, output_filename)
            if not os.path.exists(output_path) and filename.endswith(".json"):
                cmd = lambda a=merge_base_folder, b=merge_extract_folder, c=filename, d=merge_keys, e=out_folder: \
                    process_chunk(a, b, c, d, e)
                if queue is not None:
                    queue.append(cmd)
                else:
                    cmd()
    return queue


def process_chunk(merge_base_folder, merge_extract_folder, filename, merge_keys, out_folder):
    os.makedirs(out_folder, exist_ok=True)
    os.makedirs(os.path.join(out_folder, "extras"), exist_ok=True)

    base_fp = os.path.join(merge_base_folder, filename)
    extract_fp = os.path.join(merge_extract_folder, filename)
    print("Merging file:", base_fp)
    print("+ with file:", extract_fp)

    with open(base_fp, 'r', encoding='utf-8') as file:
        script_chunk = file.read()
        base_dict = json.loads(script_chunk)

    with open(extract_fp, 'r', encoding='utf-8') as file:
        script_chunk = file.read()
        extract_dict = json.loads(script_chunk)

    for key in merge_keys:
        if key in extract_dict:
            base_dict[key] = extract_dict[key]
    result = json.dumps(sort_keys(base_dict), indent=4)

    output_path = os.path.join(out_folder, filename)
    if result and len(result):
        with open(output_path, 'w', encoding='utf-8') as file:
            file.writelines(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        usage="""merge_prompts takes in two folders with the /group/story/chunk.json structure and merges
prompts from the first folder with specific key/value pairs of prompts from the second folder.

python -m tools.merge_prompts --base_folder base --merge_folder merge --output_folder out --keys test""")
    parser.add_argument('--base_folder', type=str, required=True, help='Input folder path. Should contain subfolders '
                        ' containing json files. The output will have all values from these jsons by default.')
    parser.add_argument('--merge_folder', type=str, required=True, help='Input folder path. Should contain subfolders '
                        ' containing json files. The output will have only the --keys values from these jsons.')
    parser.add_argument('--output_folder', type=str, required=True, help='Output folder path. Will be populated by a '
                        ' mirrored structure as the input folder, with modified json files.')
    parser.add_argument('--keys', nargs='+', dest='keys', required=True, help='The keys to copy over.')
    args = parser.parse_args()

    queue = []
    for f in os.listdir(args.base_folder):
        fp = os.path.join(args.base_folder, f)
        if not os.path.isdir(fp):
            continue
        process_folder_chunk_pass(
            fp,
            os.path.join(args.merge_folder, f),
            args.keys,
            os.path.join(args.out_folder, f),
            queue=queue)
    for cmd in tqdm.tqdm(queue):
        cmd()
