import uuid as uuid_module
from pathlib import Path


def pair_lines_with_timing(raw_lines: list[dict]) -> list[dict]:
    """Group raw lyric lines into timed pairs for ProPresenter slides.

    Each pair gets a start_time from the first line and a stop_time equal to
    the next pair's start_time (chained), except the last pair which uses the
    final line's end time.
    """
    clean = [l for l in raw_lines if l.get("text", "").strip()]
    if not clean:
        return []

    pairs = []
    for i in range(0, len(clean), 2):
        group = clean[i : i + 2]
        pairs.append(
            {
                "text": "\n".join(l["text"].strip() for l in group),
                "start_time": group[0]["start"],
                "stop_time": group[-1]["end"],
            }
        )

    for i in range(len(pairs) - 1):
        pairs[i]["stop_time"] = pairs[i + 1]["start_time"]

    return pairs


def build_presentation(song: dict, wav_path: Path, index: int) -> dict:
    """Build a ProPresenter-compatible JSON presentation dict for a song."""
    pairs = pair_lines_with_timing(song.get("lines", []))

    slides = [
        {
            "enabled": True,
            "notes": "",
            "text": pair["text"],
            "label": "",
            "size": {"width": 1920, "height": 1080},
            "start time": pair["start_time"],
            "stop time": pair["stop_time"],
        }
        for pair in pairs
    ]

    pres_path = (
        Path.home()
        / "Documents"
        / "ProPresenter"
        / "Libraries"
        / "Default"
        / f"{song['title']}.pro"
    )

    return {
        "presentation": {
            "id": {
                "uuid": str(uuid_module.uuid4()).upper(),
                "name": song["title"],
                "index": index,
                "audio": str(wav_path.resolve()),
            },
            "groups": [
                {
                    "name": "",
                    "color": None,
                    "slides": slides,
                }
            ],
            "has_timeline": False,
            "presentation_path": str(pres_path),
            "destination": "presentation",
        }
    }
