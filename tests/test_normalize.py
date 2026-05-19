import pytest
import torch
import torchaudio
from propresenter_jamendo.normalize import normalize_peak


def _save_wav(path, waveform, sample_rate=8000):
    torchaudio.save(str(path), waveform, sample_rate, encoding="PCM_F", bits_per_sample=32)


def _load_max_amp(path):
    waveform, _ = torchaudio.load(str(path))
    return waveform.abs().max().item()


class TestNormalizePeak:
    def test_quiet_audio_scaled_to_full(self, tmp_path):
        wav = tmp_path / "quiet.wav"
        waveform = 0.25 * torch.sin(torch.linspace(0, 6.28, 8000)).unsqueeze(0)
        _save_wav(wav, waveform)
        normalize_peak(wav)
        assert _load_max_amp(wav) == pytest.approx(1.0, abs=1e-4)

    def test_already_full_scale_unchanged(self, tmp_path):
        wav = tmp_path / "loud.wav"
        waveform = torch.sin(torch.linspace(0, 6.28, 8000)).unsqueeze(0)
        # Force max to exactly 1.0
        waveform = waveform / waveform.abs().max()
        _save_wav(wav, waveform)
        normalize_peak(wav)
        assert _load_max_amp(wav) == pytest.approx(1.0, abs=1e-4)

    def test_silence_not_modified(self, tmp_path):
        wav = tmp_path / "silence.wav"
        _save_wav(wav, torch.zeros(1, 8000))
        normalize_peak(wav)  # must not raise or divide by zero
        assert _load_max_amp(wav) == pytest.approx(0.0, abs=1e-6)

    def test_negative_peak_handled(self, tmp_path):
        # Waveform with negative peak louder than positive peak
        wav = tmp_path / "neg.wav"
        waveform = torch.full((1, 8000), -0.4)
        _save_wav(wav, waveform)
        normalize_peak(wav)
        loaded, _ = torchaudio.load(str(wav))
        assert loaded.abs().max().item() == pytest.approx(1.0, abs=1e-4)

    def test_output_is_32bit_float(self, tmp_path):
        wav = tmp_path / "out.wav"
        waveform = 0.5 * torch.ones(1, 8000)
        _save_wav(wav, waveform)
        normalize_peak(wav)
        info = torchaudio.info(str(wav))
        assert info.bits_per_sample == 32
        assert info.encoding == "PCM_F"

    def test_multichannel_normalized_by_global_peak(self, tmp_path):
        wav = tmp_path / "stereo.wav"
        left = 0.3 * torch.ones(1, 8000)
        right = 0.6 * torch.ones(1, 8000)
        waveform = torch.cat([left, right], dim=0)
        _save_wav(wav, waveform)
        normalize_peak(wav)
        loaded, _ = torchaudio.load(str(wav))
        # Global peak (0.6) should become 1.0; left channel scales by same factor
        assert loaded.abs().max().item() == pytest.approx(1.0, abs=1e-4)
        assert loaded[0].abs().max().item() == pytest.approx(0.5, abs=1e-4)
