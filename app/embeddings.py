import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


# ----- Paths (relative to repo root) -----
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
SONGS_PATH = DATA_DIR / "songs.json"

# Output files we will generate
VECTORS_PATH = DATA_DIR / "song_vectors.npy"
TEXTS_PATH = DATA_DIR / "song_texts.json"


def _as_list(value):
    """Normalize strings/lists into a list of strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        v = value.strip()
        return [v] if v else []
    return [str(value).strip()]


def build_song_text(song: dict) -> str:
    """
    Build the combined text we embed for a song.
    We include facets + vibe tags + description so semantic search can benefit
    from your metadata design.
    """
    title = str(song.get("title", "")).strip()
    artists = _as_list(song.get("artist"))

    moods = _as_list(song.get("mood"))
    activities = _as_list(song.get("activity"))
    energy = str(song.get("energy", "")).strip()
    genres = _as_list(song.get("genre"))
    vibe_tags = _as_list(song.get("vibe_tags"))

    description = str(song.get("description", "")).strip()

    # Combine structured tags into a compact "tag string"
    tags = []
    tags += [f"title: {title}"] if title else []
    tags += [f"artist: {', '.join(artists)}"] if artists else []
    tags += [f"mood: {', '.join(moods)}"] if moods else []
    tags += [f"activity: {', '.join(activities)}"] if activities else []
    tags += [f"energy: {energy}"] if energy else []
    tags += [f"genre: {', '.join(genres)}"] if genres else []
    tags += [f"vibe: {', '.join(vibe_tags)}"] if vibe_tags else []

    # Final text: tags + description
    parts = []
    if tags:
        parts.append(" | ".join(tags))
    if description:
        parts.append(description)

    return "\n".join(parts).strip()


def main():
    if not SONGS_PATH.exists():
        raise FileNotFoundError(f"Could not find {SONGS_PATH}")

    # Load dataset
    songs = json.loads(SONGS_PATH.read_text(encoding="utf-8"))
    if not isinstance(songs, list) or len(songs) == 0:
        raise ValueError("songs.json must be a non-empty list of song objects.")

    # Build texts to embed
    song_texts = [build_song_text(song) for song in songs]

    # Load embedding model (small + fast + good enough for this project)
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Compute embeddings
    vectors = model.encode(song_texts, show_progress_bar=True, normalize_embeddings=True)

    # Save outputs
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    np.save(VECTORS_PATH, vectors)
    TEXTS_PATH.write_text(json.dumps(song_texts, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Saved vectors to: {VECTORS_PATH}")
    print(f"Saved embedded texts to: {TEXTS_PATH}")
    print(f"Songs: {len(songs)} | Vector shape: {vectors.shape}")


if __name__ == "__main__":
    main()