from pathlib import Path
import json
import re
from collections import Counter

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

def main() -> None:
    tracks_path = DATA_PROCESSED / "tracks.json"
    tracks = load_tracks(tracks_path)

    for t in tracks:
        t["track_id"] = make_track_id(t)

if __name__ == "__main__":
    main()
