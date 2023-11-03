import sentencepiece as spm


sp = spm.SentencePieceProcessor(
    model_file=r'library\tokenizer\tokenizer.model')


def get_token_count(text: str) -> int:
    tokenized = sp.encode(text, out_type=str)
    return len(tokenized)