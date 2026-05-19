from unittest.mock import patch
from propresenter_jamendo.audio import download_audio

FAKE_SONG = {"title": "My Song", "file_name": "audio/My_Song.mp3"}

# normalize_peak is always mocked here — its own tests live in test_normalize.py
MOCK_NORMALIZE = patch("propresenter_jamendo.audio.normalize_peak")


class TestDownloadAudio:
    def test_downloads_from_correct_repo_path(self, tmp_path):
        with patch("propresenter_jamendo.audio.hf_hub_download",
                   return_value="/fake/My_Song.mp3") as mock_dl, \
             patch("propresenter_jamendo.audio.subprocess.run"), MOCK_NORMALIZE:
            download_audio(FAKE_SONG, tmp_path)
        mock_dl.assert_called_once_with(
            "jamendolyrics/jam-alt",
            "subsets/en/audio/My_Song.mp3",
            repo_type="dataset",
        )

    def test_returns_wav_path_in_output_dir(self, tmp_path):
        with patch("propresenter_jamendo.audio.hf_hub_download", return_value="/fake/My_Song.mp3"), \
             patch("propresenter_jamendo.audio.subprocess.run"), MOCK_NORMALIZE:
            result = download_audio(FAKE_SONG, tmp_path)
        assert result == tmp_path / "My Song.wav"

    def test_wav_extension(self, tmp_path):
        with patch("propresenter_jamendo.audio.hf_hub_download", return_value="/fake/My_Song.mp3"), \
             patch("propresenter_jamendo.audio.subprocess.run"), MOCK_NORMALIZE:
            result = download_audio(FAKE_SONG, tmp_path)
        assert result.suffix == ".wav"

    def test_calls_ffmpeg_with_correct_args(self, tmp_path):
        wav_path = tmp_path / "My Song.wav"
        with patch("propresenter_jamendo.audio.hf_hub_download", return_value="/fake/My_Song.mp3"), \
             patch("propresenter_jamendo.audio.subprocess.run") as mock_run, MOCK_NORMALIZE:
            download_audio(FAKE_SONG, tmp_path)
        args = mock_run.call_args[0][0]
        assert args[0] == "ffmpeg"
        assert "-i" in args
        assert "/fake/My_Song.mp3" in args
        assert str(wav_path) in args

    def test_ffmpeg_overwrite_flag(self, tmp_path):
        with patch("propresenter_jamendo.audio.hf_hub_download", return_value="/fake/My_Song.mp3"), \
             patch("propresenter_jamendo.audio.subprocess.run") as mock_run, MOCK_NORMALIZE:
            download_audio(FAKE_SONG, tmp_path)
        assert "-y" in mock_run.call_args[0][0]

    def test_normalize_called_after_ffmpeg(self, tmp_path):
        with patch("propresenter_jamendo.audio.hf_hub_download", return_value="/fake/My_Song.mp3"), \
             patch("propresenter_jamendo.audio.subprocess.run"), \
             patch("propresenter_jamendo.audio.normalize_peak") as mock_norm:
            result = download_audio(FAKE_SONG, tmp_path)
        mock_norm.assert_called_once_with(result)
