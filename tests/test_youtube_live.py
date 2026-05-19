from pathlib import Path
from unittest.mock import patch, MagicMock

from propresenter_jamendo.youtube_live import (
    get_studio_duration,
    _is_live_candidate,
    _search_candidates,
    _download_from_url,
    find_and_download_live,
)

SONG_WITH_DURATION = {
    "title": "Give Me the Same",
    "artist": "HILA",
    "duration": 180.0,
    "lines": [
        {"start": 0.0, "end": 2.0, "text": "Line one"},
        {"start": 2.5, "end": 180.0, "text": "Line two"},
    ],
}

SONG_WITH_LINES_ONLY = {
    "title": "Give Me the Same",
    "artist": "HILA",
    "lines": [
        {"start": 0.0, "end": 2.0, "text": "Line one"},
        {"start": 2.5, "end": 180.0, "text": "Line two"},
    ],
}

SONG_NO_DURATION = {
    "title": "Give Me the Same",
    "artist": "HILA",
}


class TestGetStudioDuration:
    def test_prefers_duration_field(self):
        assert get_studio_duration(SONG_WITH_DURATION) == 180.0

    def test_falls_back_to_max_line_end(self):
        assert get_studio_duration(SONG_WITH_LINES_ONLY) == 180.0

    def test_returns_none_when_no_data(self):
        assert get_studio_duration(SONG_NO_DURATION) is None

    def test_returns_none_for_empty_lines(self):
        assert get_studio_duration({"title": "x", "lines": []}) is None


class TestIsLiveCandidate:
    def test_accepts_title_with_live(self):
        video = {"title": "HILA - Give Me the Same (Live at Cafe)", "duration": 240.0, "uploader": "HILA"}
        assert _is_live_candidate(video, studio_duration=180.0, artist="HILA") is True

    def test_accepts_title_with_concert(self):
        video = {"title": "HILA - Concert Session 2023", "duration": 240.0, "uploader": "HILA"}
        assert _is_live_candidate(video, studio_duration=180.0, artist="HILA") is True

    def test_accepts_title_with_acoustic(self):
        video = {"title": "HILA - Acoustic Live", "duration": 240.0, "uploader": "HILA"}
        assert _is_live_candidate(video, studio_duration=180.0, artist="HILA") is True

    def test_accepts_title_with_unplugged(self):
        video = {"title": "HILA - Unplugged Session", "duration": 240.0, "uploader": "HILA"}
        assert _is_live_candidate(video, studio_duration=180.0, artist="HILA") is True

    def test_rejects_studio_title(self):
        video = {"title": "HILA - Give Me the Same (Official Audio)", "duration": 240.0, "uploader": "HILA"}
        assert _is_live_candidate(video, studio_duration=180.0, artist="HILA") is False

    def test_rejects_duration_too_close_to_studio(self):
        # 183s is only 1.7% longer than 180s — within 10% tolerance
        video = {"title": "HILA - Give Me the Same (Live)", "duration": 183.0, "uploader": "HILA"}
        assert _is_live_candidate(video, studio_duration=180.0, artist="HILA") is False

    def test_accepts_when_duration_differs_enough(self):
        # 240s is 33% longer than 180s — clearly a different performance
        video = {"title": "HILA - Give Me the Same (Live)", "duration": 240.0, "uploader": "HILA"}
        assert _is_live_candidate(video, studio_duration=180.0, artist="HILA") is True

    def test_accepts_without_duration_info(self):
        # No duration available — title + artist check is sufficient
        video = {"title": "HILA - Give Me the Same (Live)", "duration": None, "uploader": "HILA"}
        assert _is_live_candidate(video, studio_duration=180.0, artist="HILA") is True

    def test_accepts_without_studio_duration(self):
        video = {"title": "HILA - Give Me the Same (Live)", "duration": 183.0, "uploader": "HILA"}
        assert _is_live_candidate(video, studio_duration=None, artist="HILA") is True

    def test_case_insensitive(self):
        video = {"title": "HILA - Give Me the Same LIVE Concert", "duration": 240.0, "uploader": "HILA"}
        assert _is_live_candidate(video, studio_duration=180.0, artist="HILA") is True

    def test_rejects_wrong_artist_in_title_and_uploader(self):
        # A cover by a different artist — "HILA" appears nowhere
        video = {"title": "SomeOtherBand - Give Me the Same (Live)", "duration": 240.0, "uploader": "SomeOtherBand"}
        assert _is_live_candidate(video, studio_duration=180.0, artist="HILA") is False

    def test_accepts_artist_in_uploader_even_if_not_in_title(self):
        # Artist name is in the channel name but not explicitly in the title
        video = {"title": "Give Me the Same (Live Session)", "duration": 240.0, "uploader": "HILA Official"}
        assert _is_live_candidate(video, studio_duration=180.0, artist="HILA") is True

    def test_accepts_artist_in_channel_field(self):
        # yt-dlp may return "channel" instead of "uploader"
        video = {"title": "Give Me the Same (Live)", "duration": 240.0, "uploader": "", "channel": "HILA Music"}
        assert _is_live_candidate(video, studio_duration=180.0, artist="HILA") is True

    def test_skips_artist_check_when_artist_empty(self):
        # No artist in metadata — fall back to title+live check only
        video = {"title": "Give Me the Same (Live)", "duration": 240.0, "uploader": "anyone"}
        assert _is_live_candidate(video, studio_duration=180.0, artist="") is True


class TestSearchCandidates:
    def test_parses_json_lines_from_stdout(self):
        fake_stdout = (
            '{"id": "abc123", "title": "HILA Live", "duration": 240}\n'
            '{"id": "def456", "title": "HILA Studio", "duration": 180}\n'
        )
        with patch("propresenter_jamendo.youtube_live.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=fake_stdout, returncode=0)
            results = _search_candidates("HILA Give Me the Same live")
        assert len(results) == 2
        assert results[0]["id"] == "abc123"

    def test_handles_entries_container(self):
        fake_stdout = '{"entries": [{"id": "abc", "title": "Live show"}, {"id": "def", "title": "Concert"}]}\n'
        with patch("propresenter_jamendo.youtube_live.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=fake_stdout, returncode=0)
            results = _search_candidates("query")
        assert len(results) == 2

    def test_skips_malformed_json(self):
        fake_stdout = '{"id": "good"}\nnot-json\n{"id": "also_good"}\n'
        with patch("propresenter_jamendo.youtube_live.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=fake_stdout, returncode=0)
            results = _search_candidates("query")
        assert len(results) == 2

    def test_passes_correct_search_prefix(self):
        with patch("propresenter_jamendo.youtube_live.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            _search_candidates("my query", max_results=5)
        cmd = mock_run.call_args[0][0]
        assert "ytsearch5:my query" in cmd


class TestDownloadFromUrl:
    def test_returns_wav_path_when_file_exists(self, tmp_path):
        wav = tmp_path / "My Song_live.wav"
        wav.touch()
        with patch("propresenter_jamendo.youtube_live.subprocess.run"):
            result_wav, _ = _download_from_url(
                "https://www.youtube.com/watch?v=abc", "My Song_live", tmp_path
            )
        assert result_wav == wav

    def test_returns_none_when_wav_missing(self, tmp_path):
        with patch("propresenter_jamendo.youtube_live.subprocess.run"):
            result_wav, result_cap = _download_from_url(
                "https://www.youtube.com/watch?v=abc", "My Song_live", tmp_path
            )
        assert result_wav is None
        assert result_cap is None

    def test_finds_srt_caption(self, tmp_path):
        wav = tmp_path / "My Song_live.wav"
        wav.touch()
        cap = tmp_path / "My Song_live.en.srt"
        cap.touch()
        with patch("propresenter_jamendo.youtube_live.subprocess.run"):
            _, result_cap = _download_from_url(
                "https://www.youtube.com/watch?v=abc", "My Song_live", tmp_path
            )
        assert result_cap == cap

    def test_finds_vtt_caption_when_no_srt(self, tmp_path):
        wav = tmp_path / "My Song_live.wav"
        wav.touch()
        cap = tmp_path / "My Song_live.en.vtt"
        cap.touch()
        with patch("propresenter_jamendo.youtube_live.subprocess.run"):
            _, result_cap = _download_from_url(
                "https://www.youtube.com/watch?v=abc", "My Song_live", tmp_path
            )
        assert result_cap == cap

    def test_passes_url_to_yt_dlp(self, tmp_path):
        with patch("propresenter_jamendo.youtube_live.subprocess.run") as mock_run:
            _download_from_url("https://www.youtube.com/watch?v=abc123", "stem", tmp_path)
        cmd = mock_run.call_args[0][0]
        assert "https://www.youtube.com/watch?v=abc123" in cmd

    def test_requests_wav_format(self, tmp_path):
        with patch("propresenter_jamendo.youtube_live.subprocess.run") as mock_run:
            _download_from_url("https://www.youtube.com/watch?v=abc", "stem", tmp_path)
        cmd = mock_run.call_args[0][0]
        assert "--audio-format" in cmd
        assert "wav" in cmd


class TestFindAndDownloadLive:
    CANDIDATES = [
        {"id": "abc123", "title": "HILA - Give Me the Same (Live at Cafe)", "duration": 240.0, "uploader": "HILA"},
        {"id": "def456", "title": "HILA - Give Me the Same (Official Audio)", "duration": 180.0, "uploader": "HILA"},
    ]

    def test_returns_none_when_no_candidates(self, tmp_path):
        with patch("propresenter_jamendo.youtube_live._search_candidates", return_value=[]):
            wav, cap, url = find_and_download_live(SONG_WITH_DURATION, tmp_path)
        assert wav is None
        assert cap is None
        assert url is None

    def test_returns_none_when_no_live_candidate_passes_filter(self, tmp_path):
        studio_only = [
            {"id": "abc", "title": "HILA - Official Audio", "duration": 180.0}
        ]
        with patch("propresenter_jamendo.youtube_live._search_candidates", return_value=studio_only):
            wav, cap, url = find_and_download_live(SONG_WITH_DURATION, tmp_path)
        assert wav is None
        assert url is None

    def test_chooses_first_live_candidate(self, tmp_path):
        wav_file = tmp_path / "Give Me the Same_live.wav"
        wav_file.touch()
        with patch("propresenter_jamendo.youtube_live._search_candidates", return_value=self.CANDIDATES), \
             patch("propresenter_jamendo.youtube_live.subprocess.run"):
            wav, _, _ = find_and_download_live(SONG_WITH_DURATION, tmp_path)
        assert wav == wav_file

    def test_returns_youtube_url(self, tmp_path):
        wav_file = tmp_path / "Give Me the Same_live.wav"
        wav_file.touch()
        with patch("propresenter_jamendo.youtube_live._search_candidates", return_value=self.CANDIDATES), \
             patch("propresenter_jamendo.youtube_live.subprocess.run"):
            _, _, url = find_and_download_live(SONG_WITH_DURATION, tmp_path)
        assert url == "https://www.youtube.com/watch?v=abc123"

    def test_output_stem_includes_live_suffix(self, tmp_path):
        wav_file = tmp_path / "Give Me the Same_live.wav"
        wav_file.touch()
        with patch("propresenter_jamendo.youtube_live._search_candidates", return_value=self.CANDIDATES), \
             patch("propresenter_jamendo.youtube_live.subprocess.run") as mock_run:
            find_and_download_live(SONG_WITH_DURATION, tmp_path)
        cmd = mock_run.call_args[0][0]
        assert "Give Me the Same_live" in " ".join(cmd)

    def test_includes_video_id_in_url(self, tmp_path):
        wav_file = tmp_path / "Give Me the Same_live.wav"
        wav_file.touch()
        with patch("propresenter_jamendo.youtube_live._search_candidates", return_value=self.CANDIDATES), \
             patch("propresenter_jamendo.youtube_live.subprocess.run") as mock_run:
            find_and_download_live(SONG_WITH_DURATION, tmp_path)
        cmd = mock_run.call_args[0][0]
        assert "abc123" in " ".join(cmd)
