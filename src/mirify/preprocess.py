from pathlib import Path
import json
import re
from collections import Counter
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

_SPACE = re.compile(r"\s+")

def norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = _SPACE.sub(" ", s)
    return s

def make_track_id(track: dict) -> str:
    artist = norm(track.get("artist", ""))
    track_name = norm(track.get("track_name", ""))
    return f"{artist} - {track_name}"
    

def load_tracks(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
    
def to_int(x: Any) -> int | None:
    try:
        return int(str(x).strip())
    except Exception:
        return None
    
def to_bool_int(x: Any) -> int | None:
    if x is None:
        return None
    s = str(x).strip().lower()
    if s in {"1", "true", "t", "yes", "y"}:
        return 1
    if s in {"0", "false", "f", "no", "n"}:
        return 0
    return None

def clean_track(track: dict[str, Any]) -> dict[str, Any] | None:
    playlist = norm(track.get("playlist", ""))
    track_name = norm(track.get("track_name", ""))
    artist = norm(track.get("artist", ""))
    album = norm(track.get("album", ""))

    position = to_int(track.get("position"))
    liked = to_bool_int(track.get("liked"))

    if not playlist or not track_name or not artist:
        return None
    if position is None or position <= 0:
        return None
    if liked is None:
        return None
    
    return {
        "playlist": playlist,
        "position": position,
        "track_name": track_name,
        "artist": artist,
        "album": album,
        "liked": liked
    }
             
def save_tracks(path: Path, tracks: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding ="utf-8") as f:
        json.dump(tracks, f, ensure_ascii=False, indent=2)

def main() -> None:
    tracks_path = DATA_PROCESSED / "tracks.json"
    tracks = load_tracks(tracks_path)

    for t in tracks:
        t["track_id"] = make_track_id(t)

    print(f"Loaded {len(tracks)} tracks")
    print(f"Sample track IDs:")
    for t in tracks[:3]:
        print(" ", t["track_id"])

    cleaned = []
    for t in tracks:
        ct = clean_track(t)
        if ct is not None:
            cleaned.append(ct)
    print(f"Sample cleaned tracks")
    for t in cleaned[:3]:
        print(t)
    
    out = DATA_PROCESSED / "tracks_clean.json"
    save_tracks(out, cleaned)
    print(f"Wrote cleaned tracks to {out}")


if __name__ == "__main__":
    main()
