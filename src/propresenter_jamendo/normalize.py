"""Peak normalization for WAV files produced by the pipeline."""
from pathlib import Path

import torch
import torchaudio


def normalize_peak(wav_path: Path) -> None:
    """Scale audio so the loudest sample reaches full scale (0 dBFS = 1.0).

    Only scales *up* — audio already at or above full scale is left untouched.
    The file is overwritten in place. Output encoding is 32-bit float PCM,
    which Audacity and ProPresenter both read without issue.
    """
    waveform, sample_rate = torchaudio.load(str(wav_path))
    max_amp = waveform.abs().max().item()
    if max_amp == 0.0 or max_amp >= 1.0:
        return
    waveform = waveform / max_amp
    torchaudio.save(str(wav_path), waveform, sample_rate, encoding="PCM_F", bits_per_sample=32)
