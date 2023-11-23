import pytest
import os
import shutil
import tempfile


def reset_test_folder(test_data_dir: str):
    if os.path.exists(test_data_dir):
        shutil.rmtree(test_data_dir)
    os.makedirs(test_data_dir)


@pytest.fixture
def create_temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def populate_files(input_folder: str, file_contents: dict[str, str]):
    for filename in file_contents:
        with open(os.path.join(input_folder, filename), 'w') as f:
            f.write(file_contents[filename])


def compare_folders(actual_folder: str, expected_folder: str):
    actual_files = os.listdir(actual_folder)
    expected_files = os.listdir(expected_folder)

    assert sorted(actual_files) == sorted(expected_files)

    for filename in actual_files:
        actual_file = os.path.join(actual_folder, filename)
        expected_file = os.path.join(expected_folder, filename)

        with open(actual_file, 'r') as f:
            actual_content = f.read()

        with open(expected_file, 'r') as f:
            expected_content = f.read()

        assert actual_content == expected_content


def check_file_for_string(folder, subpath, strings_to_check):
    file_path = os.path.join(folder, subpath)
    assert os.path.isfile(file_path), f"File '{file_path}' does not exist."
    with open(file_path, 'r') as f:
        file_contents = f.read()
        for string_to_check in strings_to_check:
            assert string_to_check in file_contents, strings_to_check[string_to_check]
