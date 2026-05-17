import json
from unittest.mock import patch
from propresenter_jamendo.cli import main

FAKE_LINES = [
    {"start": 0.0, "end": 1.0, "text": "Line A\n"},
    {"start": 1.0, "end": 2.0, "text": "Line B\n"},
    {"start": 2.0, "end": 3.0, "text": "Line C\n"},
]

FAKE_SONGS = [
    {
        "title": "Song One",
        "language": "en",
        "file_name": "audio/Song_One.mp3",
        "lines": FAKE_LINES,
        "text": "",
    },
    {
        "title": 'Bad:Title/Test',
        "language": "en",
        "file_name": "audio/Bad_Title.mp3",
        "lines": FAKE_LINES,
        "text": "",
    },
]


def _run_main(tmp_path, songs=None):
    with patch("propresenter_jamendo.cli.download_english_songs",
               return_value=songs if songs is not None else FAKE_SONGS), \
         patch("propresenter_jamendo.audio.hf_hub_download", return_value="/fake/audio.mp3"), \
         patch("propresenter_jamendo.audio.subprocess.run"), \
         patch("sys.argv", ["cli", "--output-dir", str(tmp_path)]):
        main()


def test_writes_txt_file(tmp_path):
    _run_main(tmp_path)
    assert (tmp_path / "Song One.txt").exists()


def test_txt_content_is_formatted(tmp_path):
    _run_main(tmp_path)
    content = (tmp_path / "Song One.txt").read_text(encoding="utf-8")
    assert content == "Line A\nLine B\n\nLine C\n"


def test_writes_json_file(tmp_path):
    _run_main(tmp_path)
    assert (tmp_path / "Song One.json").exists()


def test_json_structure(tmp_path):
    _run_main(tmp_path)
    data = json.loads((tmp_path / "Song One.json").read_text())
    p = data["presentation"]
    assert p["id"]["name"] == "Song One"
    assert p["has_timeline"] is False
    assert p["destination"] == "presentation"
    slides = p["groups"][0]["slides"]
    assert len(slides) == 2
    assert "start time" in slides[0]
    assert "stop time" in slides[0]


def test_json_audio_path_points_to_wav(tmp_path):
    _run_main(tmp_path)
    data = json.loads((tmp_path / "Song One.json").read_text())
    audio = data["presentation"]["id"]["audio"]
    assert audio.endswith(".wav")
    assert "Song One" in audio


def test_sanitizes_filename(tmp_path):
    _run_main(tmp_path)
    assert (tmp_path / "BadTitleTest.txt").exists()
    assert (tmp_path / "BadTitleTest.json").exists()


def test_creates_output_dir_if_missing(tmp_path):
    nested = tmp_path / "a" / "b" / "c"
    with patch("propresenter_jamendo.cli.download_english_songs", return_value=[]), \
         patch("sys.argv", ["cli", "--output-dir", str(nested)]):
        main()
    assert nested.is_dir()
