import argparse
import json
from pathlib import Path

from propresenter_jamendo.audio import download_audio
from propresenter_jamendo.downloader import download_english_songs, extract_lines
from propresenter_jamendo.formatter import format_lyrics, safe_filename
from propresenter_jamendo.presentation import build_presentation
from propresenter_jamendo.youtube_live import find_and_download_live, get_studio_duration


def _format_duration(seconds: float | None) -> str | None:
    if seconds is None:
        return None
    total = int(seconds)
    return f"{total // 60}:{total % 60:02d}"


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
    parser.add_argument(
        "--youtube-live",
        action="store_true",
        help=(
            "Search YouTube for a live performance of each song "
            "and download it as <name>_live.wav (plus captions if available)"
        ),
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("Downloading Jamendo dataset…")
    songs = download_english_songs()
    print(f"Found {len(songs)} English songs.\n")

    # Load previously found results keyed by (artist, song) for O(1) lookup.
    # Entries with reject="yes" are kept in the map so the program never re-searches them.
    # Entries with reject="no" are re-downloaded if the audio file is missing from disk.
    results_path = args.output_dir / "found-live-results.json"
    entries_map: dict[tuple[str, str], dict] = {}
    if args.youtube_live and results_path.exists():
        for entry in json.loads(results_path.read_text(encoding="utf-8")):
            entries_map[(entry["artist"], entry["song"])] = entry

    for i, song in enumerate(songs):
        name = safe_filename(song["title"])
        artist = song.get("artist", "unknown artist")
        print(f"  [{i + 1}/{len(songs)}] {song['title']} — {artist}")

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

        # Optional: YouTube live performance
        if args.youtube_live:
            title = song.get("title", "")
            key = (artist, title)
            existing = entries_map.get(key)

            if existing and existing.get("reject", "no") == "yes":
                print("    → rejected (skipping)")
            elif existing:
                live_wav_path = args.output_dir / f"{safe_filename(title)}_live.wav"
                if live_wav_path.exists():
                    print("    → already found (skipping)")
                else:
                    # Audio was deleted or never saved — re-download
                    print("    → audio missing, re-downloading…")
                    live_wav, live_cap, live_url = find_and_download_live(song, args.output_dir)
                    if live_wav:
                        existing["youtube_url"] = live_url
                        existing["captions_available"] = "yes" if live_cap else "no"
                        print(f"    → live audio: {live_wav.name}")
                        if live_cap:
                            print(f"    → captions: {live_cap.name}")
                    else:
                        # Can't recover — remove so the next run will try again
                        del entries_map[key]
                        print("    → no live performance found")
            else:
                print("    → searching YouTube for live performance…")
                live_wav, live_cap, live_url = find_and_download_live(song, args.output_dir)
                if live_wav:
                    entries_map[key] = {
                        "artist": artist,
                        "song": title,
                        "duration": _format_duration(get_studio_duration(song)),
                        "youtube_url": live_url,
                        "captions_available": "yes" if live_cap else "no",
                        "reject": "no",
                    }
                    print(f"    → live audio: {live_wav.name}")
                    if live_cap:
                        print(f"    → captions: {live_cap.name}")
                else:
                    print("    → no live performance found")

    print(f"\nDone. {len(songs)} songs written to {args.output_dir}")
    if args.youtube_live:
        found_count = sum(
            1 for e in entries_map.values() if e.get("reject", "no") != "yes"
        )
        print(f"Live performances found: {found_count}/{len(songs)}")
        results_path.write_text(
            json.dumps(list(entries_map.values()), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Results written to {results_path}")


if __name__ == "__main__":
    main()
