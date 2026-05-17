# ProPresenter Jamendo

Downloads the [Jamendo jam-alt dataset](https://huggingface.co/datasets/jamendolyrics/jam-alt) and generates ProPresenter-ready files for all 20 English songs.

For each song the CLI produces three files in the output directory:

| File | Description |
|------|-------------|
| `<Title>.txt` | Paired lyric lines for manual ProPresenter import |
| `<Title>.wav` | Audio converted from the dataset's MP3 |
| `<Title>.json` | ProPresenter presentation with per-slide timing |

## Requirements

- Python 3.13 (3.12+ supported)
- [Poetry](https://python-poetry.org/) 2.x
- [ffmpeg](https://ffmpeg.org/) (for MP3 → WAV conversion)

Install ffmpeg via Homebrew if needed:

```bash
brew install ffmpeg
```

## Setup

```bash
# Use Python 3.13 to create the venv (required for pyarrow/datasets wheels)
/opt/homebrew/bin/python3.13 -m venv venv
source venv/bin/activate

# Install dependencies
poetry install
```

## Usage

```bash
source venv/bin/activate
poetry run propresenter-jamendo --output-dir ./output
```

The first run downloads the dataset and audio files from HuggingFace (~1 GB total).
Subsequent runs use the local HuggingFace cache and are fast.

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
│       ├── cli.py            # CLI entry point (--output-dir)
│       ├── downloader.py     # Fetches English metadata.jsonl from HuggingFace
│       ├── formatter.py      # Pairs lyric lines, sanitizes filenames
│       ├── audio.py          # Downloads MP3 and converts to WAV via ffmpeg
│       └── presentation.py   # Builds ProPresenter-compatible JSON
├── tests/                    # Pytest suite (mirrors src/ structure)
├── venv/                     # Local virtual environment (not committed)
├── pyproject.toml            # Poetry dependency declarations
├── poetry.toml               # Poetry local config (disables internal venv)
└── CLAUDE.md                 # AI assistant conventions
```
