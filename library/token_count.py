import sentencepiece as spm


sp = spm.SentencePieceProcessor(
    model_file=r'library\tokenizer\tokenizer.model')


def get_token_count(text: str) -> int:
    tokenized = sp.encode(text, out_type=str)
    return len(tokenized)


def get_tokens(text: str) -> list[str]:
    return sp.encode(text, out_type=str)


def decode_tokens(tokens: list[str]) -> str:
    return sp.Decode(tokens)
