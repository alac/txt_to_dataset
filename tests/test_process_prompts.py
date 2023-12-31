import os
import pytest
from unittest import mock

from .. import process_prompts
from library import settings_manager
from tests import folder_utils


@pytest.fixture()
def test_settings(request):
    settings_manager.settings.override_settings(r"tests\process_prompts_shared\test_settings.toml")

    def teardown():
        settings_manager.settings.remove_override_settings()

    request.addfinalizer(teardown)


@mock.patch('library.few_shot_request.run_ai_request')
def test_generate_prompts(mock_run_request, test_settings):
    in_folder = r"tests\process_prompts_generate\in"
    out_folder = r"tests\process_prompts_generate\out"
    expected_folder = r"tests\process_prompts_generate\expected"
    folder_utils.reset_test_folder(out_folder)

    response1 = """>Prompt: Write a scene where
- The main character is a brave young woman named Liz who is travelling alone.
- Liz encounters two men trying to rob her on a muddy street
- She intimidates them into backing down without a fight
>Male Characters: N/A
>Female Characters: Liz"""
    response2 = """>Prompt: Write a scene where
- The main character is a lonely woman who sitting by the fire reading a book during a stormy night
- the storm intensifies, causing the power to go out
- she opens the window to feel the rain and wind
- she tries to continue reading but can't concentrate due to the storm
>Male Characters: N/A
>Female Characters: unnamed woman"""
    mock_run_request.side_effect = [response1, response2]
    process_prompts.process_prompts(in_folder, out_folder, "MODE_GENERATE_PROMPT")

    folder_utils.compare_folders(
        os.path.join(out_folder, "garbage"),
        os.path.join(expected_folder, "garbage"))

    folder_utils.reset_test_folder(out_folder)


@mock.patch.object(process_prompts, 'randomize_names')
def test_randomize_names(mock_randomize_names, test_settings):
    in_folder = r"tests\process_prompts_randomize\in"
    out_folder = r"tests\process_prompts_randomize\out"
    expected_folder = r"tests\process_prompts_randomize\expected"
    folder_utils.reset_test_folder(out_folder)

    prompt_dict1 = {"story": "apple"}
    replacements1 = {"tom": "jerry"}
    prompt_dict2 = {"story": "banana"}
    replacements2 = {"bert": "ernie", "itchy": "scratchy"}

    mock_randomize_names.side_effect = [(prompt_dict1, replacements1), (prompt_dict2, replacements2)]
    process_prompts.process_prompts(in_folder, out_folder, "MODE_RANDOMIZE_NAMES")

    call_1_dict = mock_randomize_names.mock_calls[0].args[0]
    assert "She stepped out into the narrow, muddy street" in call_1_dict["story"]
    assert len(mock_randomize_names.mock_calls[0].args[1]) > 0, "Female names must be passed in"
    assert len(mock_randomize_names.mock_calls[0].args[2]) > 0, "Male names must be passed in"

    call_2_dict = mock_randomize_names.mock_calls[1].args[0]
    assert "Write a scene where\n- The main character is a lonely woman" in call_2_dict["prompt"]

    folder_utils.compare_folders(
        os.path.join(out_folder, "garbage"),
        os.path.join(expected_folder, "garbage"))

    folder_utils.reset_test_folder(out_folder)
