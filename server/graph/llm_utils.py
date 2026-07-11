def compact_text(value: str, max_chars: int) -> str:
    """Keep prompts below provider TPM limits while preserving both ends."""
    if not value or len(value) <= max_chars:
        return value or ""

    head_chars = max_chars // 2
    tail_chars = max_chars - head_chars
    omitted = len(value) - max_chars
    return (
        value[:head_chars].rstrip()
        + f"\n\n[... omitted {omitted} characters to fit model limits ...]\n\n"
        + value[-tail_chars:].lstrip()
    )
