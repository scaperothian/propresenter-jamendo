"""YouTube live-performance search and download for propresenter-jamendo."""
import json
import subprocess
from pathlib import Path

from propresenter_jamendo.formatter import safe_filename

LIVE_KEYWORDS = frozenset({"live", "concert", "session", "acoustic", "unplugged"})
# If a YouTube video's duration is within this fraction of the studio track, skip it —
# it's likely the studio recording re-uploaded with "live" in the title.
DURATION_TOLERANCE = 0.10


def get_studio_duration(song: dict) -> float | None:
    """Return the studio track duration in seconds from song metadata."""
    if "duration" in song:
        return float(song["duration"])
    lines = song.get("lines", [])
    if lines:
        return max((line.get("end", 0.0) for line in lines), default=None)
    return None


def _search_candidates(query: str, max_results: int = 8) -> list[dict]:
    """Search YouTube via yt-dlp and return full metadata for each candidate."""
    result = subprocess.run(
        [
            "yt-dlp",
            "--dump-json",
            "--no-playlist",
            f"ytsearch{max_results}:{query}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    candidates = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            if "entries" in data:
                candidates.extend(e for e in data["entries"] if e)
            else:
                candidates.append(data)
        except json.JSONDecodeError:
            continue
    return candidates


def _is_live_candidate(video: dict, studio_duration: float | None, artist: str = "") -> bool:
    """Return True if this video looks like a genuine live performance by the right artist."""
    title = (video.get("title") or "").lower()
    duration = video.get("duration")

    if not any(kw in title for kw in LIVE_KEYWORDS):
        return False

    # Verify the artist appears in the title or the YouTube channel name so that
    # covers and tribute performances by other artists are rejected.
    if artist:
        artist_lower = artist.lower()
        uploader = (video.get("uploader") or video.get("channel") or "").lower()
        if artist_lower not in title and artist_lower not in uploader:
            return False

    if studio_duration and duration:
        ratio = abs(duration - studio_duration) / studio_duration
        if ratio < DURATION_TOLERANCE:
            # Too close to studio length — likely a studio track re-uploaded as "live"
            return False

    return True


def _download_from_url(url: str, stem: str, output_dir: Path) -> tuple[Path | None, Path | None]:
    """Download audio and captions from a YouTube URL.

    Returns (wav_path, caption_path). Either may be None on failure or absence.
    """
    output_template = str(output_dir / f"{stem}.%(ext)s")
    subprocess.run(
        [
            "yt-dlp",
            "-x",
            "--audio-format", "wav",
            "--write-subs",
            "--write-auto-subs",
            "--sub-langs", "en",
            "--convert-subs", "srt",
            "--no-playlist",
            "-o", output_template,
            url,
        ],
        capture_output=True,
        check=False,
    )

    wav_path = output_dir / f"{stem}.wav"
    if not wav_path.exists():
        return None, None

    caption_path = None
    for ext in ("srt", "vtt"):
        for path in output_dir.glob(f"{stem}*.{ext}"):
            caption_path = path
            break
        if caption_path:
            break

    return wav_path, caption_path


def download_live_from_url(
    url: str, song: dict, output_dir: Path
) -> tuple[Path | None, Path | None]:
    """Download a live performance from a specific YouTube URL.

    Used when the user has manually updated youtube_url in found-live-results.json.
    Returns (wav_path, caption_path). Either may be None on failure.
    """
    stem = safe_filename(song.get("title", "")) + "_live"
    return _download_from_url(url, stem, output_dir)


def find_and_download_live(
    song: dict, output_dir: Path
) -> tuple[Path | None, Path | None, str | None]:
    """Search YouTube for a live performance and download audio + captions.

    Searches for the song by artist and title with "live" appended, then filters
    candidates by title keywords and duration (to avoid studio re-uploads).

    Returns (wav_path, caption_path, youtube_url). Any value may be None if no
    matching video was found or if download failed.
    """
    title = song.get("title", "")
    artist = song.get("artist", "")
    studio_duration = get_studio_duration(song)
    query = f"{artist} {title} live".strip()

    candidates = _search_candidates(query)
    chosen = next(
        (v for v in candidates if _is_live_candidate(v, studio_duration, artist)), None
    )
    if chosen is None:
        return None, None, None

    video_id = chosen.get("id")
    if not video_id:
        return None, None, None

    url = f"https://www.youtube.com/watch?v={video_id}"
    stem = safe_filename(title) + "_live"
    wav_path, caption_path = _download_from_url(url, stem, output_dir)
    return wav_path, caption_path, url
