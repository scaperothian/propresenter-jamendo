import argparse
import json
from pathlib import Path

from propresenter_jamendo.audio import download_audio
from propresenter_jamendo.downloader import download_english_songs, extract_lines
from propresenter_jamendo.formatter import format_lyrics, safe_filename
from propresenter_jamendo.presentation import build_presentation


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate ProPresenter files from Jamendo English songs."
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        metavar="DIR",
        help="Directory where .txt, .wav, and .json files will be written",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("Downloading Jamendo dataset…")
    songs = download_english_songs()
    print(f"Found {len(songs)} English songs.\n")

    for i, song in enumerate(songs):
        name = safe_filename(song["title"])
        print(f"  [{i + 1}/{len(songs)}] {song['title']}")

        # Lyrics text file
        lines = extract_lines(song)
        (args.output_dir / f"{name}.txt").write_text(
            format_lyrics(lines), encoding="utf-8"
        )

        # Audio WAV
        print("    → downloading audio…")
        wav_path = download_audio(song, args.output_dir)

        # ProPresenter JSON presentation
        pres = build_presentation(song, wav_path, index=i)
        (args.output_dir / f"{name}.json").write_text(
            json.dumps(pres, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    print(f"\nDone. {len(songs)} songs written to {args.output_dir}")


if __name__ == "__main__":
    main()
