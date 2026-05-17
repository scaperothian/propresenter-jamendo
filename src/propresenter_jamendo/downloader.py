import json
from huggingface_hub import hf_hub_download

REPO_ID = "jamendolyrics/jam-alt"


def download_english_songs() -> list[dict]:
    """Download English song metadata from the jam-alt dataset.

    Loads subsets/en/metadata.jsonl directly via huggingface_hub to avoid
    the torchcodec dependency that datasets triggers when encoding audio.
    Each record includes title, lyrics text, timed lines, and an audio
    file_name path for future audio tasks.
    """
    local_path = hf_hub_download(REPO_ID, "subsets/en/metadata.jsonl", repo_type="dataset")
    with open(local_path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def extract_lines(song: dict) -> list[str]:
    """Extract ordered lyric lines from a song record.

    Prefers the structured `lines` field; falls back to splitting `text`.
    """
    if song.get("lines"):
        return [entry["text"] for entry in song["lines"]]
    return song.get("text", "").splitlines()
