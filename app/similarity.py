import json
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
from sentence_transformers import SentenceTransformer


# ----- Paths (relative to repo root) -----
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"

SONGS_PATH = DATA_DIR / "songs.json"
VECTORS_PATH = DATA_DIR / "song_vectors.npy"


# We keep the model name identical to embeddings.py so query + songs share a vector space.
MODEL_NAME = "all-MiniLM-L6-v2"


def load_songs() -> List[Dict[str, Any]]:
    if not SONGS_PATH.exists():
        raise FileNotFoundError(f"Could not find {SONGS_PATH}")
    songs = json.loads(SONGS_PATH.read_text(encoding="utf-8"))
    if not isinstance(songs, list) or len(songs) == 0:
        raise ValueError("songs.json must be a non-empty list of song objects.")
    return songs


def load_vectors() -> np.ndarray:
    if not VECTORS_PATH.exists():
        raise FileNotFoundError(
            f"Could not find {VECTORS_PATH}. Run: python app/embeddings.py"
        )
    vectors = np.load(VECTORS_PATH)
    if vectors.ndim != 2:
        raise ValueError(f"Expected a 2D array of vectors, got shape: {vectors.shape}")
    return vectors


def _ensure_top_k(top_k: int, n_items: int) -> int:
    if top_k <= 0:
        return 5
    return min(top_k, n_items)


def semantic_search(
    query: str,
    top_k: int = 5,
    model: SentenceTransformer | None = None,
) -> List[Dict[str, Any]]:
    """
    Return the top_k songs most similar to the query (cosine similarity).
    Assumes song vectors were saved with normalize_embeddings=True,
    so dot(query_vec, song_vec) == cosine similarity.
    """
    query = (query or "").strip()
    if not query:
        return []

    songs = load_songs()
    song_vectors = load_vectors()

    if len(songs) != song_vectors.shape[0]:
        raise ValueError(
            f"Mismatch: songs.json has {len(songs)} songs but song_vectors has "
            f"{song_vectors.shape[0]} vectors. Re-run embeddings.py after editing songs.json."
        )

    top_k = _ensure_top_k(top_k, len(songs))

    # Load model once (caller can pass a cached model)
    model = model or SentenceTransformer(MODEL_NAME)

    # Embed query (normalized so dot product becomes cosine similarity)
    query_vec = model.encode([query], normalize_embeddings=True)[0]  # shape (384,)

    # Compute similarity to all songs
    scores = song_vectors @ query_vec  # shape (num_songs,)

    # Get indices of top_k scores (descending)
    top_idx = np.argsort(scores)[::-1][:top_k]

    results: List[Dict[str, Any]] = []
    for idx in top_idx:
        song = songs[int(idx)]
        results.append(
            {
                "score": float(scores[int(idx)]),
                **song,  # include title/artist/facets/description/etc.
            }
        )

    return results


if __name__ == "__main__":
    # Quick local test
    test_query = "soft dreamy songs for late night walking"
    hits = semantic_search(test_query, top_k=5)
    print(f"Query: {test_query}\n")
    for i, h in enumerate(hits, start=1):
        print(f"{i}. {h.get('title')} — {h.get('artist')}  (score={h['score']:.3f})")