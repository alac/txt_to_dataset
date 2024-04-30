import os


def get_subpaths_to_process(in_folder: str, out_folder: str) -> list[str]:
    """
    for every file in a subfolder of in_folder, return the subpath relative to in_folder.
    except if a parallel file exists in the out_folder.
    assumes the output file will be a json.

    :param in_folder:
    :param out_folder:
    :return:
    """
    subpaths_filenames = []

    for subfolder in os.listdir(in_folder):
        if not os.path.isdir(os.path.join(in_folder, subfolder)):
            continue
        for filename in os.listdir(os.path.join(in_folder, subfolder)):
            if os.path.isdir(os.path.join(in_folder, subfolder, filename)):
                continue
            out_path = os.path.join(out_folder, subfolder, filename.replace(".txt", ".json"))
            if os.path.isfile(out_path):
                continue
            subpaths_filenames.append(os.path.join(subfolder, filename))
    return sorted(subpaths_filenames)


def write_output_and_debug_files(out_folder: str, filename: str, result: str, debug_files: dict[str,str]):
    os.makedirs(out_folder, exist_ok=True)

    output_path = os.path.join(out_folder, filename)
    if result and len(result):
        with open(output_path, 'w', encoding='utf-8') as file:
            file.writelines(result)
    if debug_files:
        for suffix, contents in debug_files.items():
            if contents:
                os.makedirs(os.path.join(out_folder, "extras"), exist_ok=True)
                output_path = os.path.join(out_folder,
                                           "extras",
                                           filename.replace(".json", f"{suffix}.json"))
                with open(output_path, 'w', encoding='utf-8') as file:
                    file.writelines(contents)
