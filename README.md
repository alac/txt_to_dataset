# text to instruction dataset
A collection of scripts used to generate the dataset for the WW-Storytelling-70B-LoRA.

Supports:
- Breaking `.txt` files into chunks based on context length.
- Using a local instance of Oobabooga (or anything that supports an OpenAI-style API) to generate prompts and other metadata.
- Outputting a final `.json` file for training with Oobabooga.
- Various tools for analyzing the dataset (count common phrases, randomize names, batch generate responses from the final model).

## Setup

1. Clone this repo.
2. Install requirements with `pip install -r requirements.txt`.
3. Edit `settings.toml` (or make a copy named `user.toml`).
    - The defaults should work out of the box, unless:
      - You're not using Oobabooga to generate prompts or it isn't being hosted on the same machine.
      - You're not working on a storytelling dataset.
        - This should still be doable, but you'll have to live with the keys being named "story", "context", "prompt".
        - See `prompt_gen.prompt_file_path` in the `settings.toml` for how to modify the prompt generation request.
4. (If generating prompts) Launch Oobabooga's Text-Generation-Webui with the API extension enabled and load a model.

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
4) Generate the `.json` file to use with your training scripts.
```
python finalize_dataset.py --input_folder IN_FOLDER1 IN_FOLDER2
    --output_folder OUT_FOLDER
# You can specify multiple input folders after the --input_folder flag
```
5) Use the `.json` dataset files in the output folder to train in Oobabooga. A compatible format file is provided in the project root directory.

## Tools

- The *COUNT_PHRASES* mode of process_prompts.py counts repeated phrases across your prompt json folders. Comparing this across two kinds of input (e.g. literature vs fanfiction) can be useful for finding phrases biases in the dataset.
- The *RANDOMIZE_NAMES* mode of process_prompts.py randomizes names in prompt json folders. Avoids name biases.
- `python -m tools.inject_hardcoded_keys` can be used to batch edit prompt jsons (e.g. add the genre, year of publication, etc.)
- `python -m tools.prompt_tester` can be used to generate sample outputs. Uses a template + list of values to cycle through.
- `python -m tools.merge_prompts` can be used to combine prompts from two different folders. This is mostly for doing partial reverts on the prompt json folders.

## Customization

You can customize how prompts are tagged by editing `processors/few_shot_templates/full_prompt.txt` and `settings.toml`.

Add new tags by adding them to the template and each example in `full_prompt.txt`. Make sure that the tags are always in the same order; the AI may start dropping tags otherwise. You can remove a tag the same way.

`json_key_order` and `allowed_fields` in `settings.toml` should be updated correspondingly. Note that tag names are all lowercase here.

## Credits

This repo contains lists of male and female names sourced from:
* https://github.com/datasets-io/female-first-names-en
* https://github.com/datasets-io/male-first-names-en

