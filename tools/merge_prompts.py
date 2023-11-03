import os
import tqdm
import json
import random

from library.prompt_parser import sort_keys


def process_folder_chunk_pass(merge_base_folder, merge_extract_folder, merge_keys, out_folder, queue=None):
    """
    queue process_chunk tasks

    :param in_folder:
    :param out_folder:
    :return:
    """
    for filename in tqdm.tqdm(os.listdir(merge_base_folder)):
        if os.path.isfile(os.path.join(merge_base_folder, filename)):
            output_filename = filename
            output_path = os.path.join(out_folder, output_filename)
            if not os.path.exists(output_path) and filename.endswith(".txt"):
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
