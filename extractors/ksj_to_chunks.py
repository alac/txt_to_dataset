import argparse
import json
import os
import re

from library.token_count import get_token_count
from library.settings_manager import ROOT_FOLDER

VN_LOCATIONS = os.path.join(ROOT_FOLDER, "ksj_locations.json")
VN_NAMES = os.path.join(ROOT_FOLDER, "ksj_names.json")
DEFAULT_NARRATOR = "NARRATOR (V.O.)"


def convert_ksj_script(in_folder: str, filename: str, out_folder: str, max_tokens: int) -> None:
    """
    Takes in a single .ksj script file and:
    - formats the contents as a screenplay, keeping narration, dialog and scene change markers.
    - outputs the contents in max_token length files (using the sentencepiece tokenizer).
    - separates out files containing roleplay actions into a separate /roleplay/ folder.
    - additionally, outputs story constants like character names and locations to files in the project root.
    - skips files that contain branches.

    :param in_folder:
    :param filename:
    :param out_folder:
    :param max_tokens:
    :return:
    """

    """
    KSJ format notes

    ;◇◇◇
    -> the ';' indicates a comment

    @hide
    -> the '@' indicates a command
    --- @nm t="XYZ" s=ABC
        t="XYZ" is the name of the character
        s=ABC is the sound file of the scene

    *p5|
    -> the '*' indicates a upcoming line of dialog (it probably hides what was there before)


    "I take thee at thy word[r]Call me but love, and I'll be new baptized"[np]
    -> the rest is dialog.
        [r] indicates a return and should be replaced with a space
        [np] indicates a newline (?)

    HOW DO THEY DO CHOICES
    * there's a block that starts with
        *branch_select_x_init
    * and a jump command later
        @jump target="*branch_select_x_2" cond="f.branch_variable == 0"

    the script starts with a key
    ;●●●：Designation of clothing:
    ;★★★: CG designation: ev1111etc.
    ;◇◇◇: background: day, evening, night, etc.
    ;♪♪♪ SE designation: where or from where/who or what/what sound
    ;¶¶¶: Flag designation: Flag ON or OFF or + or ETC
    ; ■■■: Branching contents : Branching by ~.
    ; ▼▼▼：Branching ：Branching by ~.
    ; ▲▲▲: Branching: Branching to here in the case of ~
    ; □□□：Branch end ：Branch merging by ~
    ;＃＃＃： Voice instruction: Acting instruction to voice actors
    ;※※※：Special direction: matters to be discussed
    """

    fp = os.path.join(in_folder, filename)
    print("Processing file:", fp)

    # read the entire file
    with open(fp, 'r', encoding='utf-16') as file:
        ksj_lines = file.readlines()

    # trash it if there's a branch
    if any([l for l in ksj_lines if l.startswith("@exlink")]):
        print("\tDiscovered a branch, exiting")

    final_script = []
    if os.path.exists(VN_LOCATIONS):
        with open(VN_LOCATIONS, "rb") as f:
            locations_map = json.load(f)
    else:
        locations_map = {}
    locations_original_and_new = set(locations_map.keys()).union(locations_map.values())

    if os.path.exists(VN_NAMES):
        with open(VN_NAMES, "rb") as f:
            all_names = json.load(f)
    else:
        all_names = {}

    # for every line...
    for l in ksj_lines:
        l = l.strip()
        # ";◇◇◇：空／昼" scene description
        if l.startswith(";◇◇◇："):
            if l.startswith(";◇◇◇：背景指定  ：～昼夕夜etc"):
                continue
            locations_map[l] = locations_map.get(l, l)
            location_line = locations_map[l] + "\n"
            if len(final_script) == 0:
                final_script.append(location_line)
            elif final_script[-1].strip() in locations_original_and_new:
                final_script[-1] = location_line
            else:
                final_script.append(location_line)
            continue
        # "@nm t="DisplayName" s=Identifier" nametag
        if l.startswith('@nm t="'):
            start_pos = l.find('"') + 1
            end_pos = l.find('"', start_pos)
            name = l[start_pos:end_pos]
            all_names[name] = name
            final_script.append(name.upper() + "\n")
            continue
        if len(l) == 0 or l[0] in ["@", ";", "*"]:
            # stage directions, comments, and line annotations. skip.
            continue
        if l[0] == r'"':
            # dialog
            l_clean = l.replace("[r]", " ").replace("[np]","").strip('"')
            final_script[-1] = final_script[-1].strip("\n") + "\n" + l_clean + "\n"
            continue
        if l[0].isalpha():
            # narration
            l_clean = l.replace("[r]", " ").replace("[np]","")
            final_script.append(f"{DEFAULT_NARRATOR}\n{l_clean}\n")
            continue

    # condense V.O.
    condensed_script = []
    for l in final_script:
        if l.startswith(DEFAULT_NARRATOR) and len(condensed_script) > 1:
            if condensed_script[-1].startswith(DEFAULT_NARRATOR):
                lines = l.split("\n")
                condensed_script[-1] = condensed_script[-1].strip("\n") + " " + lines[1] + "\n"
                continue
        condensed_script.append(l)

    with open(VN_LOCATIONS, 'w') as f:
        json.dump(locations_map, f, ensure_ascii=False, indent=2)
    with open(VN_NAMES, 'w') as f:
        json.dump(all_names, f, ensure_ascii=False, indent=2)

    os.makedirs(out_folder, exist_ok=True)
    out_folder_roleplay = os.path.join(out_folder, "roleplay")
    os.makedirs(out_folder_roleplay, exist_ok=True)

    last_location = ""
    current_chunk = ""
    chunk_index = 0
    for i, l in enumerate(condensed_script):
        if l.strip() in locations_original_and_new:
            last_location = l.strip()
        else:
            if current_chunk == "" and last_location != "":
                current_chunk = last_location + "\n"
        prev_chunk = current_chunk
        current_chunk += l
        token_count = get_token_count(current_chunk)

        if token_count > max_tokens or i == len(condensed_script) - 1:
            # get rid of roleplay tags *UWU*
            pattern = r'\*.*?\*'  # Regular expression pattern to match *BLAH*
            matches = re.findall(pattern, prev_chunk)
            if not matches:
                output_path = get_file_chunk_output_path(filename, chunk_index, out_folder)
            else:
                output_path = get_file_chunk_output_path(filename, chunk_index, out_folder_roleplay)
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(prev_chunk)
            current_chunk = ""
            chunk_index += 1


def get_file_output_path(filename: str, prompts_folder: str) -> str:
    chunk_name, extension = os.path.splitext(filename)
    out_name = f"{chunk_name}.txt"
    return os.path.join(prompts_folder, out_name)


def get_file_chunk_output_path(filename: str, index: int, prompts_folder: str) -> str:
    chunk_name, extension = os.path.splitext(filename)
    out_name = f"{chunk_name}_chunk_{index}.txt"
    return os.path.join(prompts_folder, out_name)


def ksj_folder_to_chunks(in_folder: str, out_folder: str, max_tokens: int) -> None:
    """
    take a folder of ksj scripts and write each converted script to the out folder

    :param in_folder:
    :param out_folder:
    :param max_tokens:
    :return:
    """
    for filename in os.listdir(in_folder):
        if os.path.isfile(os.path.join(in_folder, filename)):
            output_path = get_file_output_path(filename, out_folder)
            if not os.path.exists(output_path) and filename.endswith(".ks"):
                convert_ksj_script(in_folder, filename, out_folder, max_tokens)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(usage="""
Takes in a folder of .ksj script files and:
- formats the contents as a screenplay, keeping narration, dialog and scene change markers.
- outputs the contents in max_token length files (using the sentencepiece tokenizer) to the output folder.
- separates out files containing roleplay actions into a separate /roleplay/ folder.
- additionally, outputs story constants like character names and locations to files in the project root.
- skips files that contain branches.

python extractors.ksj_to_chunks  --input_folder /in --output_folder /out --max_tokens 1700'
""")
    parser.add_argument('--input_folder', type=str, required=True, help='Input folder path. Should contain txt files '
                        'to be split into max_token length files.')
    parser.add_argument('--output_folder', type=str, required=True, help='Output folder path. An input file "Derp.ksj" '
                        'will have output chunks written to {output_folder}/Derp_chunk_*.txt')
    parser.add_argument('--max_tokens', type=int, required=True, help='Maximum number of tokens in each output file. \n'
                        'Splits at paragraph boundaries, so the actual length of output files will vary. \n'
                        'Uses the default tokenizer for Llama and Llama2 (sentencepiece) to determine token count. \n'
                        'max_tokens should be your training length minus your expected prompt length. \n')
    args = parser.parse_args()
    ksj_folder_to_chunks(args.input_folder, args.output_folder, args.max_tokens)

