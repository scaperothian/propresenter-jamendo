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
        "artist": "Artist A",
        "language": "en",
        "file_name": "audio/Song_One.mp3",
        "duration": 3.0,
        "lines": FAKE_LINES,
        "text": "",
    },
    {
        "title": "Bad:Title/Test",
        "artist": "Artist B",
        "language": "en",
        "file_name": "audio/Bad_Title.mp3",
        "duration": 3.0,
        "lines": FAKE_LINES,
        "text": "",
    },
]


def _run_main(tmp_path, songs=None, extra_argv=None):
    argv = ["cli", "--output-dir", str(tmp_path)] + (extra_argv or [])
    with patch("propresenter_jamendo.cli.download_english_songs",
               return_value=songs if songs is not None else FAKE_SONGS), \
         patch("propresenter_jamendo.audio.hf_hub_download", return_value="/fake/audio.mp3"), \
         patch("propresenter_jamendo.audio.subprocess.run"), \
         patch("propresenter_jamendo.audio.normalize_peak"), \
         patch("sys.argv", argv):
        main()


def _run_main_with_live(tmp_path, live_return, songs=None):
    """Run main with --youtube-live, mocking find_and_download_live."""
    with patch("propresenter_jamendo.cli.find_and_download_live",
               return_value=live_return):
        _run_main(tmp_path, songs=songs, extra_argv=["--youtube-live"])


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


RESULTS_FILE = "found-live-results.json"


class TestLiveResults:
    URL = "https://www.youtube.com/watch?v=abc123"

    def test_results_file_created_when_performance_found(self, tmp_path):
        wav = tmp_path / "Song One_live.wav"
        wav.touch()
        _run_main_with_live(
            tmp_path, live_return=(wav, None, self.URL), songs=[FAKE_SONGS[0]]
        )
        assert (tmp_path / RESULTS_FILE).exists()

    def test_results_file_not_created_without_flag(self, tmp_path):
        _run_main(tmp_path)
        assert not (tmp_path / RESULTS_FILE).exists()

    def test_only_found_songs_in_file(self, tmp_path):
        wav = tmp_path / "Song One_live.wav"
        wav.touch()
        # First song found, second not found
        side_effects = [(wav, None, self.URL), (None, None, None)]
        with patch("propresenter_jamendo.cli.find_and_download_live",
                   side_effect=side_effects):
            _run_main(tmp_path, extra_argv=["--youtube-live"])
        data = json.loads((tmp_path / RESULTS_FILE).read_text())
        assert len(data) == 1
        assert data[0]["song"] == "Song One"

    def test_entry_fields_when_found(self, tmp_path):
        wav = tmp_path / "Song One_live.wav"
        cap = tmp_path / "Song One_live.en.srt"
        wav.touch()
        cap.touch()
        _run_main_with_live(
            tmp_path,
            live_return=(wav, cap, self.URL),
            songs=[FAKE_SONGS[0]],
        )
        entry = json.loads((tmp_path / RESULTS_FILE).read_text())[0]
        assert entry["artist"] == "Artist A"
        assert entry["song"] == "Song One"
        assert entry["duration"] == "0:03"
        assert entry["youtube_url"] == self.URL
        assert entry["captions_available"] == "yes"

    def test_captions_no_when_wav_found_but_no_captions(self, tmp_path):
        wav = tmp_path / "Song One_live.wav"
        wav.touch()
        _run_main_with_live(
            tmp_path,
            live_return=(wav, None, self.URL),
            songs=[FAKE_SONGS[0]],
        )
        entry = json.loads((tmp_path / RESULTS_FILE).read_text())[0]
        assert entry["captions_available"] == "no"

    def test_duration_formatting(self, tmp_path):
        wav = tmp_path / "Song One_live.wav"
        wav.touch()
        song = {**FAKE_SONGS[0], "duration": 125.0}
        _run_main_with_live(tmp_path, live_return=(wav, None, self.URL), songs=[song])
        entry = json.loads((tmp_path / RESULTS_FILE).read_text())[0]
        assert entry["duration"] == "2:05"

    def test_new_entry_has_reject_no_by_default(self, tmp_path):
        wav = tmp_path / "Song One_live.wav"
        wav.touch()
        _run_main_with_live(
            tmp_path, live_return=(wav, None, self.URL), songs=[FAKE_SONGS[0]]
        )
        entry = json.loads((tmp_path / RESULTS_FILE).read_text())[0]
        assert entry["reject"] == "no"

    def test_new_entry_has_downloaded_url(self, tmp_path):
        wav = tmp_path / "Song One_live.wav"
        wav.touch()
        _run_main_with_live(
            tmp_path, live_return=(wav, None, self.URL), songs=[FAKE_SONGS[0]]
        )
        entry = json.loads((tmp_path / RESULTS_FILE).read_text())[0]
        assert entry["downloaded_url"] == self.URL

    def test_skips_when_audio_present(self, tmp_path):
        wav = tmp_path / "Song One_live.wav"
        wav.touch()
        existing = [{
            "artist": "Artist A", "song": "Song One", "duration": "0:03",
            "youtube_url": self.URL, "downloaded_url": self.URL,
            "captions_available": "no", "reject": "no",
        }]
        (tmp_path / RESULTS_FILE).write_text(json.dumps(existing), encoding="utf-8")
        with patch("propresenter_jamendo.cli.find_and_download_live") as mock_search, \
             patch("propresenter_jamendo.cli.download_live_from_url") as mock_dl:
            _run_main(tmp_path, songs=[FAKE_SONGS[0]], extra_argv=["--youtube-live"])
        mock_search.assert_not_called()
        mock_dl.assert_not_called()

    def test_redownloads_when_audio_missing(self, tmp_path):
        # Entry is in JSON but WAV file is absent — re-downloads from stored URL
        existing = [{
            "artist": "Artist A", "song": "Song One", "duration": "0:03",
            "youtube_url": self.URL, "downloaded_url": self.URL,
            "captions_available": "no", "reject": "no",
        }]
        (tmp_path / RESULTS_FILE).write_text(json.dumps(existing), encoding="utf-8")
        wav = tmp_path / "Song One_live.wav"
        with patch("propresenter_jamendo.cli.download_live_from_url",
                   return_value=(wav, None)) as mock_dl:
            _run_main(tmp_path, songs=[FAKE_SONGS[0]], extra_argv=["--youtube-live"])
        mock_dl.assert_called_once()

    def test_removed_from_file_when_redownload_fails(self, tmp_path):
        # Entry is in JSON, audio is gone, re-download also fails → removed from file
        existing = [{
            "artist": "Artist A", "song": "Song One", "duration": "0:03",
            "youtube_url": self.URL, "downloaded_url": self.URL,
            "captions_available": "no", "reject": "no",
        }]
        (tmp_path / RESULTS_FILE).write_text(json.dumps(existing), encoding="utf-8")
        with patch("propresenter_jamendo.cli.download_live_from_url",
                   return_value=(None, None)):
            _run_main(tmp_path, songs=[FAKE_SONGS[0]], extra_argv=["--youtube-live"])
        data = json.loads((tmp_path / RESULTS_FILE).read_text())
        assert data == []

    # --- URL-change cases (Option A) ---

    def test_redownloads_when_url_changed(self, tmp_path):
        # User edited youtube_url to a new value — should fetch the new URL
        new_url = "https://www.youtube.com/watch?v=NEW999"
        existing = [{
            "artist": "Artist A", "song": "Song One", "duration": "0:03",
            "youtube_url": new_url, "downloaded_url": self.URL,
            "captions_available": "no", "reject": "no",
        }]
        (tmp_path / RESULTS_FILE).write_text(json.dumps(existing), encoding="utf-8")
        wav = tmp_path / "Song One_live.wav"
        with patch("propresenter_jamendo.cli.download_live_from_url",
                   return_value=(wav, None)) as mock_dl:
            _run_main(tmp_path, songs=[FAKE_SONGS[0]], extra_argv=["--youtube-live"])
        mock_dl.assert_called_once()
        args_used = mock_dl.call_args[0]
        assert args_used[0] == new_url

    def test_downloaded_url_updated_after_url_change(self, tmp_path):
        new_url = "https://www.youtube.com/watch?v=NEW999"
        existing = [{
            "artist": "Artist A", "song": "Song One", "duration": "0:03",
            "youtube_url": new_url, "downloaded_url": self.URL,
            "captions_available": "no", "reject": "no",
        }]
        (tmp_path / RESULTS_FILE).write_text(json.dumps(existing), encoding="utf-8")
        wav = tmp_path / "Song One_live.wav"
        wav.touch()
        with patch("propresenter_jamendo.cli.download_live_from_url",
                   return_value=(wav, None)):
            _run_main(tmp_path, songs=[FAKE_SONGS[0]], extra_argv=["--youtube-live"])
        entry = json.loads((tmp_path / RESULTS_FILE).read_text())[0]
        assert entry["downloaded_url"] == new_url

    def test_url_change_not_triggered_when_urls_match(self, tmp_path):
        # Both fields are the same — should not call download_live_from_url for URL-change
        wav = tmp_path / "Song One_live.wav"
        wav.touch()
        existing = [{
            "artist": "Artist A", "song": "Song One", "duration": "0:03",
            "youtube_url": self.URL, "downloaded_url": self.URL,
            "captions_available": "no", "reject": "no",
        }]
        (tmp_path / RESULTS_FILE).write_text(json.dumps(existing), encoding="utf-8")
        with patch("propresenter_jamendo.cli.download_live_from_url") as mock_dl:
            _run_main(tmp_path, songs=[FAKE_SONGS[0]], extra_argv=["--youtube-live"])
        mock_dl.assert_not_called()

    def test_old_entry_without_downloaded_url_not_redownloaded(self, tmp_path):
        # Entries created before downloaded_url was added should not trigger re-download
        wav = tmp_path / "Song One_live.wav"
        wav.touch()
        existing = [{
            "artist": "Artist A", "song": "Song One", "duration": "0:03",
            "youtube_url": self.URL, "captions_available": "no", "reject": "no",
            # no downloaded_url field
        }]
        (tmp_path / RESULTS_FILE).write_text(json.dumps(existing), encoding="utf-8")
        with patch("propresenter_jamendo.cli.download_live_from_url") as mock_dl:
            _run_main(tmp_path, songs=[FAKE_SONGS[0]], extra_argv=["--youtube-live"])
        mock_dl.assert_not_called()

    def test_skips_rejected_songs(self, tmp_path):
        existing = [{
            "artist": "Artist A", "song": "Song One", "duration": "0:03",
            "youtube_url": self.URL, "captions_available": "no", "reject": "yes",
        }]
        (tmp_path / RESULTS_FILE).write_text(json.dumps(existing), encoding="utf-8")
        with patch("propresenter_jamendo.cli.find_and_download_live") as mock_live:
            _run_main(tmp_path, songs=[FAKE_SONGS[0]], extra_argv=["--youtube-live"])
        mock_live.assert_not_called()

    def test_rejected_song_not_counted_in_summary(self, tmp_path, capsys):
        existing = [{
            "artist": "Artist A", "song": "Song One", "duration": "0:03",
            "youtube_url": self.URL, "captions_available": "no", "reject": "yes",
        }]
        (tmp_path / RESULTS_FILE).write_text(json.dumps(existing), encoding="utf-8")
        _run_main(tmp_path, songs=[FAKE_SONGS[0]], extra_argv=["--youtube-live"])
        output = capsys.readouterr().out
        assert "Live performances found: 0/1" in output

    def test_rejected_entry_preserved_in_file(self, tmp_path):
        # reject=yes entry must survive the run (so it keeps being skipped)
        existing = [{
            "artist": "Artist A", "song": "Song One", "duration": "0:03",
            "youtube_url": self.URL, "captions_available": "no", "reject": "yes",
        }]
        (tmp_path / RESULTS_FILE).write_text(json.dumps(existing), encoding="utf-8")
        _run_main(tmp_path, songs=[FAKE_SONGS[0]], extra_argv=["--youtube-live"])
        data = json.loads((tmp_path / RESULTS_FILE).read_text())
        assert len(data) == 1
        assert data[0]["reject"] == "yes"

    def test_existing_results_preserved_across_runs(self, tmp_path):
        existing = [{
            "artist": "Artist A", "song": "Song One", "duration": "0:03",
            "youtube_url": self.URL, "captions_available": "no", "reject": "no",
        }]
        (tmp_path / RESULTS_FILE).write_text(json.dumps(existing), encoding="utf-8")
        wav_first = tmp_path / "Song One_live.wav"
        wav_first.touch()
        wav_second = tmp_path / "BadTitleTest_live.wav"
        wav_second.touch()
        # First song skipped (audio present); second song found
        _run_main_with_live(tmp_path, live_return=(wav_second, None, self.URL))
        data = json.loads((tmp_path / RESULTS_FILE).read_text())
        songs_in_file = {e["song"] for e in data}
        assert "Song One" in songs_in_file
        assert "Bad:Title/Test" in songs_in_file
