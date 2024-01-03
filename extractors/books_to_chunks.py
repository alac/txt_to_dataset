import argparse
import os
import tqdm

from library.english_constants import abbreviated_titles
from library.token_count import get_token_count, get_tokens, decode_tokens

LINE_ENDINGS = (".", "?", "'", '"')


def break_text_into_chunks(input_file: str, output_folder: str, max_tokens: int, exclude_if_too_long: bool) -> None:
    print("book_to_chunks processing: ", input_file)
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.read()
    # strip BOM since str.strip() won't do it.
    if ord(content[0]) == 65279:
        content = content[1:]

    paragraphs = preprocess_text(content)
    paragraphs = apply_token_cap_to_paragraphs(paragraphs, exclude_if_too_long, max_tokens-1)

    chunks = []
    start_index = 0
    end_index = 0
    token_count = 0

    for index, paragraph in tqdm.tqdm(enumerate(paragraphs), "processing paragraphs"):
        paragraph_tokens = get_token_count(paragraph)

        # pad token count by 1 for newline
        if token_count + paragraph_tokens + 1 < max_tokens:
            end_index = index
            token_count = token_count + paragraph_tokens + 1
        else:
            chunks.append("\n".join(paragraphs[start_index:end_index+1]))
            start_index = index
            end_index = index
            token_count = paragraph_tokens

        if index == len(paragraphs) - 1:
            chunks.append("\n".join(paragraphs[start_index:end_index+1]))

    # Write chunks to separate text files in the output folder
    os.makedirs(output_folder, exist_ok=True)
    for i, chunk in enumerate(chunks):
        output_file = os.path.join(output_folder, f"chunk_{i + 1}.txt")
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(chunk)


def preprocess_text(content: str) -> list[str]:
    """
    Take a text input and split it into a list of paragraphs with the following properties:
    - undo line wrapping.
    - normalize quotes.
    - (attempt) to throw out lines with trivial content (e.g. chapter markers, TITLES).

    :param content:
    :return:
    """
    content = content.replace("’", "'")
    lines = content.split("\n")

    paragraphs = []
    current_paragraph = []

    def is_paragraph_start(l: str) -> bool:
        char = l[0]
        if char.isnumeric() or (char.isalpha() and char.isupper()):
            return True
        if char in ["'"]:
            return True
        return False

    def is_end_of_paragraph(l: str) -> bool:
        title = [t for t in abbreviated_titles if l.endswith(t)]
        if any(title):
            return False
        return l.endswith(LINE_ENDINGS)

    for line in lines:
        line = line.strip()
        if len(line) == 0:
            continue
        if line.isnumeric():
            continue
        if line.lower().startswith("chapter"):
            current_paragraph.append("\n")
            continue

        if len(current_paragraph) > 0 or is_paragraph_start(line):
            current_paragraph.append(line)
        else:
            continue

        if is_end_of_paragraph(line):
            paragraphs.append(" ".join(current_paragraph))
            current_paragraph = []

    if current_paragraph:
        paragraphs.append("\n".join(current_paragraph))

    return paragraphs


def apply_token_cap_to_paragraphs(paragraphs: list[str], exclude_if_too_long: bool, max_tokens: int):
    result = []
    for paragraph in paragraphs:
        tokens = get_tokens(paragraph)
        if len(tokens) <= max_tokens:
            result.append(paragraph)
        elif exclude_if_too_long:
            continue
        else:
            remaining_tokens = tokens
            print(len(tokens))
            while len(remaining_tokens):
                if len(remaining_tokens) < max_tokens - 1:
                    result.append(decode_tokens(remaining_tokens))
                    break
                end_token = max_tokens - 1
                keep, carry = None, None
                while end_token > 0:
                    print(end_token, "end token", remaining_tokens[end_token])
                    if "." == remaining_tokens[end_token]:
                        keep, carry = remaining_tokens[end_token], None
                        break
                    if "▁" == remaining_tokens[end_token][0]:
                        keep, carry = None, remaining_tokens[end_token]
                        break
                    if "▁" == remaining_tokens[end_token][-1]:
                        keep, carry = remaining_tokens[end_token], None
                        break
                    end_token = end_token - 1
                fragment_tokens = remaining_tokens[:end_token]
                if keep:
                    fragment_tokens.append(keep)
                result.append(decode_tokens(fragment_tokens))
                remaining_tokens = remaining_tokens[end_token+1:]
                if carry:
                    remaining_tokens = [carry] + remaining_tokens
    return result


def books_to_chunks(in_folder: str, out_folder: str, max_tokens: int, exclude_if_too_long: bool = False):
    for f in os.listdir(in_folder):
        if not f.endswith(".txt"):
            continue
        break_text_into_chunks(os.path.join(in_folder, f),
                               os.path.join(out_folder, f.replace(".txt", "")),
                               max_tokens,
                               exclude_if_too_long=exclude_if_too_long)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        usage='Takes a folder of text files breaks each into max_token length files. \n'
              'python -m extractors.books_to_chunks --input_folder /in --output_folder /out --max_tokens 1700')
    parser.add_argument('--input_folder', type=str, required=True, help='Input folder path. Should contain txt files '
                        'to be split into max_token length files.')
    parser.add_argument('--output_folder', type=str, required=True, help='Output folder path. An input file "Derp.txt" '
                        'will have output chunks written to {output_folder}/Derp/.')
    parser.add_argument('--max_tokens', type=int, required=True, help='Maximum number of tokens in each output file. \n'
                        'Splits at paragraph boundaries, so the actual length of output files will vary. \n'
                        'Uses the default tokenizer for Llama and Llama2 (sentencepiece) to determine token count. \n'
                        'max_tokens should be your training length minus your expected prompt length. \n')
    parser.add_argument('-exclude', action='store_true', help='Excludes paragraphs that are longer than max_tokens. \n'
                        'By default, excessively long paragraphs will be broken at word boundaries. \n')

    args = parser.parse_args()
    books_to_chunks(args.input_folder, args.output_folder, args.max_tokens, args.exclude)
