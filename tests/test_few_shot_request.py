from unittest import mock

from library.few_shot_request import edit_few_shot_request, parse_few_shot_format, few_shot_request


def test_parse_few_shot_format_single_entry():
    prompt = ">name: John\n>age: 23\n>biography: This is a paragraph."
    result = parse_few_shot_format(prompt)
    assert len(result) == 1
    assert result[0] == {
        "name": "John",
        "age": "23",
        "biography": "This is a paragraph.",
    }


def test_parse_few_shot_format_multiple_entries():
    prompt = ">name: John\n>age: 23\n>biography: This is a paragraph.\n\n>name: Bill\n>age: 42\n>biography: This is "\
             "another paragraph.\n\n"
    result = parse_few_shot_format(prompt)
    assert len(result) == 2
    assert result[0] == {
        "name": "John",
        "age": "23",
        "biography": "This is a paragraph.",
    }
    assert result[1] == {
        "name": "Bill",
        "age": "42",
        "biography": "This is another paragraph.",
    }


def test_parse_few_shot_format_multiline_value():
    prompt = ">name: John\n>age: 23\n>biography: This is a paragraph.\nThis is a continuation of the paragraph.\n\n"
    result = parse_few_shot_format(prompt)
    assert len(result) == 1
    assert result[0] == {
        "name": "John",
        "age": "23",
        "biography": "This is a paragraph.\nThis is a continuation of the paragraph.",
    }


def test_parse_few_shot_format_empty_lines():
    prompt = ">name: John\n>age: 23\n\n>biography: This is a paragraph.\n\n>name: Bill\n>age: 42\n\n"
    result = parse_few_shot_format(prompt)
    assert len(result) == 3
    assert result[0] == {
        "name": "John",
        "age": "23",
    }
    assert result[1] == {
        "biography": "This is a paragraph.",
    }
    assert result[2] == {
        "name": "Bill",
        "age": "42",
    }


def test_edit_few_shot_request_none():
    few_shot_example = """>name: John
>age: 23
>biography: paragraph1
paragraph2
paragraph3
>shoe size: 20

>name: John
>age: 23
>biography: paragraph1
paragraph2
paragraph3"""
    edited_few_shot = edit_few_shot_request(few_shot_example, [])
    assert edited_few_shot == few_shot_example, "Check edit_few_shot_request works without edits"


def test_edit_few_shot_request_remove_keys():
    few_shot_example = """>name: John
>age: 23
>biography: paragraph1
paragraph2
paragraph3
>shoe size: 20

>name: John
>age: 23
>biography: paragraph1
paragraph2
paragraph3"""
    edited_few_shot = edit_few_shot_request(few_shot_example, ["age", "biography"])
    assert edited_few_shot == """>name: John
>shoe size: 20

>name: John""", "Check edit_few_shot_request works with edits"

    edited_few_shot = edit_few_shot_request(few_shot_example, ["age", "biography", "team"])
    assert edited_few_shot == """>name: John
>shoe size: 20

>name: John""", "Check edit_few_shot_request works even when trying to remove a key that isn't there"


@mock.patch('library.few_shot_request.run_ai_request')
def test_few_shot_request(mock_run_request):
    expected_ai_request = """>Name: The Sunshine Gang
>Excess1: blah blah
blah
blah
>Taste: Dirty
>Location: Earth
>Excess2: blah

>Name: Steve
>Excess1: blah blah
blah
blah"""
    intended_ai_response = """>Taste: Dirty
>Location: Earth
>Excess2: blah
"""

    mock_run_request.return_value = intended_ai_response
    result = few_shot_request("tests/few_shot_request_data/test_request.txt", {"name": "Steve"})

    assert mock_run_request.called
    assert mock_run_request.call_args == mock.call(
        expected_ai_request,
        custom_stopping_strings=["\n>Name:", "Name:"],
        temperature=0.7,
        max_response=600,
        ban_eos_token=True)

    assert result == {"Taste": "Dirty", "Location": "Earth"}
