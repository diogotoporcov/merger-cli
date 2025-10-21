def parse_escape_chars(text: str) -> str:
    return (
        text
        .replace("\\n", "\n")
        .replace("\\t", "\t")
    )