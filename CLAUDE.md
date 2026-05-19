# CLAUDE.md — Project Conventions for AI Assistants

This file describes how work should be done in this repository. Follow these rules in every session.

## Git Workflow

- The default branch is `main`. **Never commit feature work directly to `main`.**
- All changes must be made in a feature branch:
  ```bash
  git checkout -b feature/<short-description>
  ```
- Merge to `main` only via a reviewed and tested PR (or explicit user instruction).
- Use descriptive commit messages in the imperative mood ("Add Jamendo search client").

## Testing

- **Run `pytest` immediately after every code change** to catch regressions.
- Tests live in `tests/`. Mirror the `src/` structure (e.g. `src/propresenter_jamendo/foo.py` → `tests/test_foo.py`).
- All new features must be accompanied by tests.
- Do not commit code that makes existing tests fail.

```bash
source venv/bin/activate
pytest
```

## Environment Management

### Virtual Environment

The project uses a **non-hidden `venv/` directory** (not `.venv/`) for the Python virtual environment.

```bash
# Create (first time only)
python3 -m venv venv

# Activate (every session)
source venv/bin/activate

# Deactivate when done
deactivate
```

The `venv/` directory is excluded from git (see `.gitignore`).

### Python Version

Python version is managed through the `venv/` directory. The interpreter baked into the venv at creation time determines the runtime Python version. To change the Python version, recreate the venv:

```bash
/path/to/target/python3 -m venv venv
```

#### VSCode Note

VSCode may not automatically pick up the `venv/` interpreter. If you see import errors or the wrong Python version in VSCode:

1. Open the Command Palette (`Cmd+Shift+P`)
2. Run **"Python: Select Interpreter"**
3. Choose `./venv/bin/python`

#### Python Version Mismatch Workaround

If you encounter a Python version mismatch error (e.g., Poetry or another tool conflicts with an existing `VIRTUALENV` environment variable), unset it:

```bash
unset VIRTUALENV
```

Then re-activate the venv normally.

### Dependency Management

Dependencies are declared in `pyproject.toml` and managed with [Poetry](https://python-poetry.org/).

`poetry.toml` sets `virtualenvs.create = false` so Poetry uses the **active venv** instead of creating its own. Always activate the venv before running Poetry commands:

```bash
source venv/bin/activate
poetry add <package>      # add a runtime dependency
poetry add --group dev <package>  # add a dev/test dependency
poetry install            # install all declared deps into active venv
```

### Critical Dependencies

| Package | Purpose |
|---------|---------|
| pytest | Test runner |
| datasets | HuggingFace dataset library |
| huggingface-hub | Download files from HuggingFace Hub |
| torch 2.7.0 | PyTorch (pinned; needed for future audio tasks) |
| torchaudio 2.7.0 | Audio I/O (pinned to match torch) |
| yt-dlp | YouTube search and audio/caption download in `youtube_live.py` |

Add new critical dependencies to this table when introduced.

### System Dependencies

| Tool | Purpose | Install |
|------|---------|---------|
| ffmpeg | MP3 → WAV conversion in `audio.py` and `youtube_live.py` | `brew install ffmpeg` |

### Python Version

This project requires **Python 3.13** (not 3.15+). The `pyarrow` and `torch` packages do not yet provide wheels for Python 3.15 alpha. If the venv was created with the wrong interpreter, recreate it:

```bash
rm -rf venv
/opt/homebrew/bin/python3.13 -m venv venv
source venv/bin/activate
poetry install
```

## Architecture

The package has one module per responsibility:

| Module | Responsibility |
|--------|---------------|
| `cli.py` | Argument parsing; orchestrates the pipeline for each song |
| `downloader.py` | Fetches `subsets/en/metadata.jsonl` from HuggingFace (no audio encoding step) |
| `formatter.py` | Groups lyric lines into pairs for `.txt` output; sanitizes filenames |
| `audio.py` | Downloads the per-song MP3 and converts to WAV via `ffmpeg` subprocess |
| `normalize.py` | Peak-normalizes a WAV file to full scale (0 dBFS) using torchaudio |
| `presentation.py` | Pairs lyric lines with timing data; builds the ProPresenter JSON structure |
| `youtube_live.py` | Searches YouTube for live performances; downloads `<name>_live.wav` + captions via `yt-dlp` |

### CLI flags

| Flag | Description |
|------|-------------|
| `--output-dir DIR` | Required. Directory where all output files are written |
| `--youtube-live` | Enable YouTube live performance search and download |

### YouTube live search logic (`youtube_live.py`)

`find_and_download_live(song, output_dir)` returns `(wav_path, caption_path, youtube_url)`.

Candidate filtering in `_is_live_candidate`:
- Title must contain at least one of: `live`, `concert`, `session`, `acoustic`, `unplugged`
- Artist name must appear in the video title **or** the YouTube channel/uploader name
- Video duration must differ from the studio track by more than 10% (rejects studio recordings re-uploaded with "live" in the title)

### `found-live-results.json` schema and lifecycle

Written to `<output-dir>/found-live-results.json` when `--youtube-live` is used. Contains **only** songs where a live performance was found. Schema per entry:

```json
{
  "artist": "HILA",
  "song": "Bad Side",
  "duration": "3:24",
  "youtube_url": "https://www.youtube.com/watch?v=...",
  "downloaded_url": "https://www.youtube.com/watch?v=...",
  "captions_available": "yes",
  "reject": "no"
}
```

`youtube_url` is the URL to use on the next download. `downloaded_url` is the URL that produced the current WAV file on disk. They are equal under normal operation; a mismatch means the user has manually changed `youtube_url` and a re-download is needed.

Skip / re-download logic (checked in this order per song):

1. Entry in JSON with `reject: yes` → skip permanently, never re-search
2. Entry in JSON and `youtube_url != downloaded_url` → re-download from `youtube_url`, update `downloaded_url` on success
3. Entry in JSON with WAV file present on disk → skip
4. Entry in JSON but WAV file **missing** → re-download from `youtube_url`
5. No entry in JSON → search YouTube

If a re-download fails the entry is removed from the JSON so the next run will try again. New entries are always written with `"reject": "no"` and `downloaded_url` equal to `youtube_url`.

**Backward compatibility:** entries written before `downloaded_url` was introduced (field absent) are treated as if `downloaded_url == youtube_url` — no spurious re-download is triggered.

### Why `metadata.jsonl` instead of `load_dataset`?

The `jamendolyrics/jam-alt` dataset uses a generator-based builder that calls `encode_example` on every record, including the audio column. Encoding audio requires `torchcodec`, which has no Python 3.13 wheel. Loading `subsets/en/metadata.jsonl` directly via `hf_hub_download` bypasses this step entirely while providing the same lyric/timing data. Audio files are downloaded separately in `audio.py`.

### JSON presentation format

Matches the schema used by `../propresenter-train`. Key fields:

- `id.audio` — absolute path to the local WAV file
- `slides[*]["start time"]` / `slides[*]["stop time"]` — note the spaces in these keys
- `stop time` of slide N equals `start time` of slide N+1 (chained)
- `has_timeline: false`, `destination: "presentation"` required by the consumer

## Project Structure

```
propresenter-jamendo/
├── src/
│   └── propresenter_jamendo/
│       ├── cli.py            # CLI entry point (--output-dir, --youtube-live)
│       ├── downloader.py     # HuggingFace metadata fetch
│       ├── formatter.py      # Lyric pairing and filename sanitization
│       ├── audio.py          # MP3 download + WAV conversion + peak normalization
│       ├── normalize.py      # Peak normalization (shared by audio.py and youtube_live.py)
│       ├── presentation.py   # ProPresenter JSON builder
│       └── youtube_live.py   # YouTube live search + yt-dlp download + peak normalization
├── tests/                    # Pytest suite (mirrors src/ structure)
├── venv/                     # Local Python environment (not in git)
├── pyproject.toml            # Dependency declarations (Poetry)
├── poetry.toml               # Poetry local config
├── .gitignore                # Python + venv gitignore
├── README.md
└── CLAUDE.md                 # This file
```

## Summary of Rules

1. Feature branches only — never work on `main`.
2. Run `pytest` after every change.
3. Always activate `venv/` before running Python or Poetry commands.
4. If Python version mismatch: `unset VIRTUALENV`.
5. If VSCode shows wrong interpreter: set it manually via "Python: Select Interpreter".
