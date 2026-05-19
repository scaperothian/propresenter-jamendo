# ProPresenter Jamendo

Downloads the [Jamendo jam-alt dataset](https://huggingface.co/datasets/jamendolyrics/jam-alt) and generates ProPresenter-ready files for all English songs. Optionally searches YouTube for a live performance of each song and downloads that audio as well.

For each song the CLI produces these files in the output directory:

| File | Description |
|------|-------------|
| `<Title>.txt` | Paired lyric lines for manual ProPresenter import |
| `<Title>.wav` | Studio audio converted from the dataset's MP3 |
| `<Title>.json` | ProPresenter presentation with per-slide timing |
| `<Title>_live.wav` | Live performance audio from YouTube (`--youtube-live` only) |
| `<Title>_live.en.srt` | Captions for the live performance, when available |
| `found-live-results.json` | Persistent record of every live performance found |

## Requirements

- Python 3.13 (3.12+ supported)
- [Poetry](https://python-poetry.org/) 2.x
- [ffmpeg](https://ffmpeg.org/) (for MP3 → WAV conversion and audio extraction)

Install ffmpeg via Homebrew if needed:

```bash
brew install ffmpeg
```

## Setup

```bash
# Use Python 3.13 to create the venv (required for pyarrow/datasets wheels)
/opt/homebrew/bin/python3.13 -m venv venv
source venv/bin/activate

# Install dependencies (includes yt-dlp)
poetry install
```

## Usage

### Studio pipeline

```bash
source venv/bin/activate
poetry run propresenter-jamendo --output-dir ./output
```

The first run downloads the dataset and audio files from HuggingFace (~1 GB total). Subsequent runs use the local HuggingFace cache and are fast.

### YouTube live performances

Add `--youtube-live` to also search YouTube for a live performance of each song:

```bash
poetry run propresenter-jamendo --output-dir ./output --youtube-live
```

For each song the program:

1. Searches YouTube for `<artist> <title> live`
2. Filters candidates — the result must have a live keyword (`live`, `concert`, `session`, `acoustic`, `unplugged`) in the title and the artist name in the title or channel, and must not be the same duration as the studio version (to reject studio recordings re-uploaded with "live" in the title)
3. Downloads the best match as `<Title>_live.wav` and saves captions (`.srt`) if the video has them

The run is **resumable** — results are stored in `found-live-results.json` and songs already in that file are skipped on subsequent runs. If the audio file is missing from disk but the entry is still in the JSON (e.g. you deleted it manually), the program re-downloads it automatically.

### Rejecting a result

If a downloaded live performance is not acceptable (wrong song, poor quality, etc.):

1. Open `found-live-results.json` in the output directory
2. Find the entry and set `"reject": "yes"`
3. Optionally delete the `_live.wav` and caption files

On the next run the program will skip that song permanently and never re-search it.

### Using a specific YouTube URL

If you find a better live performance manually and want the program to download it:

1. Open `found-live-results.json`
2. Change `"youtube_url"` to the new URL (leave `"downloaded_url"` unchanged)
3. Save the file and re-run with `--youtube-live`

The program detects that `youtube_url` and `downloaded_url` differ, fetches the new video, and updates `downloaded_url` to match on success.

`found-live-results.json` only contains songs where a live performance was successfully found. Its schema:

```json
[
  {
    "artist": "HILA",
    "song": "Bad Side",
    "duration": "3:24",
    "youtube_url": "https://www.youtube.com/watch?v=...",
    "downloaded_url": "https://www.youtube.com/watch?v=...",
    "captions_available": "yes",
    "reject": "no"
  }
]
```

### Output format

**Lyrics text file** (`<Title>.txt`) — pairs of lines separated by blank lines:

```
Lay awake at night
Wondering how could I

Let it get this way
Through all the pain
```

**JSON presentation** (`<Title>.json`) — matches the `propresenter-train` schema:

```json
{
  "presentation": {
    "id": {
      "uuid": "...",
      "name": "Give Me The Same",
      "index": 0,
      "audio": "/absolute/path/to/Give Me The Same.wav"
    },
    "groups": [{
      "name": "",
      "color": null,
      "slides": [{
        "enabled": true,
        "notes": "",
        "text": "Lay awake at night\nWondering how could I",
        "label": "",
        "size": {"width": 1920, "height": 1080},
        "start time": 18.62,
        "stop time": 23.02
      }]
    }],
    "has_timeline": false,
    "presentation_path": "~/Documents/ProPresenter/Libraries/Default/<Title>.pro",
    "destination": "presentation"
  }
}
```

## Development

All feature work must be done in a feature branch — never directly on `main`.

```bash
git checkout -b feature/my-feature
# ... make changes ...
pytest
```

## Running Tests

```bash
source venv/bin/activate
pytest
```

## Project Structure

```
propresenter-jamendo/
├── src/
│   └── propresenter_jamendo/
│       ├── cli.py            # CLI entry point (--output-dir, --youtube-live)
│       ├── downloader.py     # Fetches English metadata.jsonl from HuggingFace
│       ├── formatter.py      # Pairs lyric lines, sanitizes filenames
│       ├── audio.py          # Downloads MP3, converts to WAV, peak-normalizes
│       ├── normalize.py      # Peak normalization to full scale (0 dBFS)
│       ├── presentation.py   # Builds ProPresenter-compatible JSON
│       └── youtube_live.py   # YouTube live search, yt-dlp download, peak-normalizes
├── tests/                    # Pytest suite (mirrors src/ structure)
├── venv/                     # Local virtual environment (not committed)
├── pyproject.toml            # Poetry dependency declarations
├── poetry.toml               # Poetry local config (disables internal venv)
└── CLAUDE.md                 # AI assistant conventions
```
