import pytest
from unittest import mock

from library import settings_manager
from processors.edit_writing import randomize_names


@pytest.fixture()
def test_settings(request):
    settings_manager.settings.override_settings(r"tests\process_prompts_shared\test_settings.toml")

    def teardown():
        settings_manager.settings.remove_override_settings()

    request.addfinalizer(teardown)


@mock.patch('processors.edit_writing.random.sample')
def test_randomize_names_one_name(mock_random_sample, test_settings):
    mock_random_sample.side_effect = [["new_first"], [], ["new_last"], []]
    result = randomize_names({
        "story": "Malefirst went to the zoo under the name dr. Malelast",
        "female characters": "",
        "male characters": "Malefirst Malelast",
    }, []
    , [""])
    assert result == ({
        "story": "new_first went to the zoo under the name dr. new_last",
        "female characters": "",
        "male characters": "new_first new_last",
    },  {'Malefirst Malelast': 'new_first new_last'})


@mock.patch('processors.edit_writing.random.sample')
def test_randomize_names_two_names(mock_random_sample, test_settings):
    mock_random_sample.side_effect = [[], ["anne", "bella"], [], ["sharlene", "rider"]]
    result = randomize_names({
        "story": "Shirley Yourekidding went to the zoo under the name dr. Tiffany Toes",
        "female characters": "Shirley Yourekidding, Tiffany Toes",
        "male characters": "",
    }, []
    , [""])
    assert result == ({
        'story': 'anne sharlene went to the zoo under the name dr. bella rider',
        "female characters":  'anne sharlene, bella rider',
        "male characters": "",
    },  {'Shirley Yourekidding': 'anne sharlene', 'Tiffany Toes': 'bella rider'})


@mock.patch('processors.edit_writing.random.sample')
def test_randomize_names_title(mock_random_sample, test_settings):
    mock_random_sample.side_effect = [[], ["anne", "bella"], [], ["sharlene", "rider"]]
    result = randomize_names({
        "story": "Shirley Yourekidding went to the zoo under the name dr. Tiffany Toes",
        "female characters": "Dr. Shirley Yourekidding, Tiffany Toes",
        "male characters": "",
    }, []
    , [""])
    assert result == ({
        "story": "Shirley Yourekidding went to the zoo under the name dr. bella rider",
        "female characters":  "Dr. Shirley Yourekidding, bella rider",
        "male characters": "",
    },  {"Tiffany Toes": "bella rider"})


@mock.patch('processors.edit_writing.random.sample')
def test_randomize_names_possessive(mock_random_sample, test_settings):
    mock_random_sample.side_effect = [[], ["anne", "bella"], [], ["sharlene", "rider"]]
    result = randomize_names({
        "story": "Shirley's brother went to the zoo under the name dr. Tiffany Toes",
        "female characters": "Shirley's Brother",
        "male characters": "",
    }, []
    , [""])
    assert result == ({
        "story": "anne's brother went to the zoo under the name dr. Tiffany Toes",
        "female characters":  "anne's Brother",
        "male characters": "",
    },  {"Shirley's Brother": "anne's Brother"})
