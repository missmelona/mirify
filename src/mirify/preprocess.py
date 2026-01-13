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
             
def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding ="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def build_track_mappings(cleaned_tracks: list[dict[str, Any]]) -> dict[str, Any]:
    uniq: dict[str, dict[str, Any]] = {}
    for t in cleaned_tracks:
        uniq[t["track_id"]] = {
            "track_name": t["track_name"],
            "artist": t["artist"],
            "album": t.get("album")
        }

    track_ids = sorted(uniq.keys())
    track_to_id = {tid: i for i, tid in enumerate(track_ids)}
    id_to_track = {str(i): uniq[tid] for tid, i in track_to_id.items()}

    return {"track_to_id": track_to_id, "id_to_track": id_to_track}

def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def make_next_track_examples(
        cleaned_tracks: list[dict[str, Any]],
        track_to_id: dict[str, int]
) -> list[dict[str, Any]]:
    by_playlist: dict[str, list[dict[str, Any]]] = {}
    for t in cleaned_tracks:
        by_playlist.setdefault(t["playlist"], []).append(t)
    for pl in by_playlist:
        by_playlist[pl].sort(key=lambda x: x["position"])

    examples: list[dict[str, Any]] = []
    for pl, items in by_playlist.items():
        if len(items) < 2:
            continue
        for prev, nxt in zip(items[:-1], items[1:]):
            examples.append(
                {
                    "playlist": pl,
                    "context_track_id": track_to_id[prev["track_id"]],
                    "target_track_id": track_to_id[nxt["track_id"]]
                }
            )
    return examples

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
        ct["track_id"] = make_track_id(ct)
    print(f"Sample cleaned tracks")
    for t in cleaned[:3]:
        print(t)
    
    out = DATA_PROCESSED / "tracks_clean.json"
    save_json(out, cleaned)
    print(f"Wrote cleaned tracks to {out}")

    mappings = build_track_mappings(cleaned)
    examples = make_next_track_examples(cleaned, mappings["track_to_id"])

    examples_path = DATA_PROCESSED / "examples.jsonl"
    mappings_path = DATA_PROCESSED / "mappings.json"

    write_jsonl(examples_path, examples)
    save_json(mappings_path, mappings)

    print(f"Wrote {len(examples)} examples to {examples_path}")
    print(f"Wrote mappings to {mappings_path}")


if __name__ == "__main__":
    main()
