import subprocess
from pathlib import Path

from huggingface_hub import hf_hub_download

from propresenter_jamendo.downloader import REPO_ID
from propresenter_jamendo.formatter import safe_filename


def download_audio(song: dict, output_dir: Path) -> Path:
    """Download the song's MP3 from HuggingFace and convert it to WAV via ffmpeg.

    file_name in the metadata (e.g. 'audio/HILA_-_Give_Me_the_Same.mp3') is
    relative to subsets/en/, so the full repo path is subsets/en/<file_name>.
    """
    repo_file = f"subsets/en/{song['file_name']}"
    mp3_path = hf_hub_download(REPO_ID, repo_file, repo_type="dataset")

    wav_path = output_dir / (safe_filename(song["title"]) + ".wav")
    subprocess.run(
        ["ffmpeg", "-i", mp3_path, "-y", str(wav_path)],
        check=True,
        capture_output=True,
    )
    return wav_path
