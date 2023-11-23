from extractors.books_to_chunks import books_to_chunks
import folder_utils
import os


def test_books_to_chunks_basic():
    in_folder = r"tests\books_to_chunks\in"
    out_folder = r"tests\books_to_chunks\out"
    expected_folder = r"tests\books_to_chunks\expected"
    folder_utils.reset_test_folder(out_folder)

    books_to_chunks(in_folder, out_folder, 200)

    folder_utils.compare_folders(os.path.join(out_folder, "the_bible"), os.path.join(expected_folder, "the_bible"))
    folder_utils.check_file_for_string(
        os.path.join(out_folder, "the_bible"),
        "chunk_3.txt",
        {
            "Mr. Smith": "Abbreviated titles shouldn't trigger a new paragraph",
            "of.\nBaalzebub": "Periods that aren't a part of a title should trigger a new paragarph"
        }
    )
    folder_utils.check_file_for_string(
        os.path.join(out_folder, "the_bible"),
        "chunk_4.txt",
        {
            "the king hath said, Come down.": "The last sentence should end the last chunk",
        }
    )

    folder_utils.reset_test_folder(out_folder)


def test_books_to_chunks_long_paragraph():
    in_folder = r"tests\books_to_chunks2\in"
    out_folder = r"tests\books_to_chunks2\out"
    expected_folder = r"tests\books_to_chunks2\expected"
    folder_utils.reset_test_folder(out_folder)

    books_to_chunks(in_folder, out_folder, 300)

    folder_utils.compare_folders(os.path.join(out_folder, "the_bible"), os.path.join(expected_folder, "the_bible"))
    chunk_1_contents = folder_utils.read_file(os.path.join(out_folder, "the_bible"),"chunk_1.txt")
    assert chunk_1_contents.startswith("Sed ut perspiciatis,")
    assert chunk_1_contents.endswith("qui dolorem")
    chunk_2_contents = folder_utils.read_file(os.path.join(out_folder, "the_bible"),"chunk_2.txt")
    assert chunk_2_contents.startswith("eum fugiat, ")
    assert chunk_2_contents.endswith("asperiores repellat.")

    folder_utils.reset_test_folder(out_folder)
