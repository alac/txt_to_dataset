# text to instruction dataset

## Setup

## Usage

1) Build a dataset in the form of a folder of `.txt` files. 
2) Turn your `.txt` files into "chunks" that you want to train the model on.
```
python -m extractors.book_to_chunks --input_folder IN_FOLDER 
    --output_folder OUT_FOLDER --max_tokens CHUNK_SIZE
# The CHUNK_SIZE should be the CUTOFF_LENGTH that you specify during training, minus your
# expected 'instruction' size (~300 tokens if using this repo's defaults).
``` 
3) Use a local model to generate prompts (see Setup for details).
```
python process_prompts.py --input_folder IN_FOLDER 
    --output_folder OUT_FOLDER --mode generate_prompts
```
4) Generate the `.jsonl` file to use with your training scripts.
```
python finalize_dataset.py --input_folder IN_FOLDER 
    --output_folder OUT_FOLDER --mode generate_prompts
# You can specify multiple input folders by repeating the --input_folder arg.
```
TODO:
## Tools


## Credits
This repo contains lists of male and female names sourced from:
* https://github.com/datasets-io/female-first-names-en
* https://github.com/datasets-io/male-first-names-en

