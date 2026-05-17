import json
import textwrap
from unittest.mock import patch, mock_open
from propresenter_jamendo.downloader import download_english_songs, extract_lines


class TestDownloadEnglishSongs:
    def _jsonl(self, rows):
        return "\n".join(json.dumps(r) for r in rows)

    def test_returns_all_rows_from_jsonl(self):
        rows = [
            {"title": "Song A", "language": "en"},
            {"title": "Song B", "language": "en"},
        ]
        fake_file = self._jsonl(rows)
        with patch("propresenter_jamendo.downloader.hf_hub_download", return_value="/fake/path"), \
             patch("builtins.open", mock_open(read_data=fake_file)):
            result = download_english_songs()
        assert len(result) == 2
        assert result[0]["title"] == "Song A"

    def test_skips_blank_lines(self):
        rows = [{"title": "Song A", "language": "en"}]
        fake_file = self._jsonl(rows) + "\n\n"
        with patch("propresenter_jamendo.downloader.hf_hub_download", return_value="/fake/path"), \
             patch("builtins.open", mock_open(read_data=fake_file)):
            result = download_english_songs()
        assert len(result) == 1

    def test_downloads_english_subset(self):
        with patch("propresenter_jamendo.downloader.hf_hub_download", return_value="/fake/path") as mock_dl, \
             patch("builtins.open", mock_open(read_data="")):
            download_english_songs()
        mock_dl.assert_called_once_with(
            "jamendolyrics/jam-alt", "subsets/en/metadata.jsonl", repo_type="dataset"
        )


class TestExtractLines:
    def test_prefers_structured_lines_field(self):
        song = {
            "lines": [
                {"start": 0.0, "end": 1.0, "text": "Hello world\n"},
                {"start": 1.0, "end": 2.0, "text": "Foo bar\n"},
            ],
            "text": "should be ignored",
        }
        assert extract_lines(song) == ["Hello world\n", "Foo bar\n"]

    def test_falls_back_to_text_field(self):
        song = {"lines": [], "text": "Line one\nLine two\n"}
        assert extract_lines(song) == ["Line one", "Line two"]

    def test_handles_missing_lines_key(self):
        song = {"text": "Only text\nHere"}
        assert extract_lines(song) == ["Only text", "Here"]

    def test_handles_empty_song(self):
        assert extract_lines({}) == []
