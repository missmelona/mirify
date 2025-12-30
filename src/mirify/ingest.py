from pathlib import Path
import json, csv, re
from dataclasses import dataclass
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

@dataclass
class Track:
    playlist: str
    position: int
    track_name: str
    artist: str
    album: str | None = None
    liked: int

_FEAT_PATTERN = re.compile(r"\s*\(feat\..*?\)|\s*\[feat\..*?\]", re.IGNORECASE)
def normalize_text(s: str) -> str:
    s = s.strip()
    s = _FEAT_PATTERN.sub("", s)
    s = re.sub(r"\s+", " ", s)
    return s

def load_tracks_from_json(path: Path, source: str = "spotify_export") -> list[Track]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    tracks: list[Track] = []
    for row in data:
        playlist = normalize_text(str(row.get("playlist", "")))
        position = row.get("position", "")
        track_name = normalize_text(str(row.get("track_name", "")))
        artist = normalize_text(str(row.get("artist", "")))
        album = normalize_text(str(row.get("album", ""))) if row.get("album") else None
        liked = row.get("liked", "")

        if not playlist or not position or not track_name or not artist or not liked:
            continue

        tracks.append(Track(playlist=playlist, position=position, track_name=track_name, artist=artist, album=album, liked=liked))
    return tracks


def load_tracks_from_csv(path: Path, source: str = "spotify_export") -> list[Track]:
    tracks: list[Track] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            playlist = normalize_text(row.get("playlist", "") or "")
            position = row.get("playlist", "") or ""
            track_name = normalize_text(row.get("track_name", "") or "")
            artist = normalize_text(row.get("artist", "") or "")
            album = normalize_text(row.get("album", "") or "") or None
            liked = row.get("liked", "") or ""

            if not playlist or not position or not track_name or not artist or not liked:
                continue

            tracks.append(Track(playlist=playlist, position=position, track_name=track_name, artist=artist, album=album, liked=liked))
    return tracks


def save_tracks_json(tracks: list[Track], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload: list[dict[str, Any]] = []
    for t in tracks:
        payload.append(
            {
                "playlist": t.playlist,
                "position": t.position,
                "track_name": t.track_name,
                "artist": t.artist,
                "album": t.album,
                "liked": t.liked,
            }
        )

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def dedupe_tracks(tracks: list[Track]) -> list[Track]:
    seen: set[tuple[str, str]] = set()
    out: list[Track] = []
    for t in tracks:
        key = (t.track_name.lower(), t.artist.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
    return out


def ingest(raw_dir: Path = DATA_RAW, processed_dir: Path = DATA_PROCESSED) -> Path:
    all_tracks: list[Track] = []

    for path in raw_dir.glob("*"):
        if path.suffix.lower() == ".json":
            all_tracks.extend(load_tracks_from_json(path))
        elif path.suffix.lower() == ".csv":
            all_tracks.extend(load_tracks_from_csv(path))

    all_tracks = dedupe_tracks(all_tracks)

    out_path = processed_dir / "tracks.json"
    save_tracks_json(all_tracks, out_path)
    return out_path


if __name__ == "__main__":
    out = ingest()
    print(f"Wrote processed dataset to: {out}")
