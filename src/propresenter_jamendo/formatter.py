import re


def format_lyrics(lines: list[str]) -> str:
    """Format a list of lyric lines into ProPresenter import format.

    Lines are grouped in pairs separated by a blank line.
    """
    clean = [l.strip() for l in lines if l.strip()]
    pairs = [clean[i : i + 2] for i in range(0, len(clean), 2)]
    return "\n\n".join("\n".join(pair) for pair in pairs) + "\n"


def safe_filename(title: str) -> str:
    """Convert a song title to a safe filesystem filename."""
    sanitized = re.sub(r'[<>:"/\\|?*]', "", title)
    sanitized = sanitized.strip(". ")
    return sanitized or "untitled"
