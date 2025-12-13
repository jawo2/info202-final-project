import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

# ----- Paths (relative to repo root) -----
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"

SONGS_PATH = DATA_DIR / "songs.json"
VECTORS_PATH = DATA_DIR / "song_vectors.npy"

# Keep identical to embeddings.py so query + songs share a vector space.
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


def _as_list(x: Any) -> List[str]:
    """Normalize a value into a list of strings."""
    if x is None:
        return []
    if isinstance(x, list):
        return [str(v).strip() for v in x if str(v).strip()]
    if isinstance(x, str):
        s = x.strip()
        return [s] if s else []
    return [str(x).strip()]


def _matches_filters(song: Dict[str, Any], filters: Dict[str, Any]) -> bool:
    """
    filters format (examples):
      {"mood": ["dreamy", "calm"], "genre": ["pop"], "energy": "medium", "activity": ["walking"]}
    Matching rule:
      - For list filters: song matches if ANY overlap
      - For scalar filters: song must equal the scalar
    """
    for key, allowed in (filters or {}).items():
        if allowed is None or allowed == [] or allowed == "":
            continue

        song_val = song.get(key)

        # list filter (multi-select)
        if isinstance(allowed, list):
            allowed_set = set(_as_list(allowed))
            song_list = set(_as_list(song_val))
            if not song_list.intersection(allowed_set):
                return False

        # scalar filter (single-select)
        else:
            if str(song_val).strip().lower() != str(allowed).strip().lower():
                return False

    return True


def semantic_search(
    query: Optional[str] = None,
    top_k: int = 5,
    model: Optional[SentenceTransformer] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Two modes:

    1) Semantic search mode (query provided):
       - Filter songs first by facets (optional)
       - Embed query
       - Rank remaining songs by cosine similarity (dot product of normalized vectors)

    2) Faceted-only mode (no query):
       - Filter songs by facets
       - Return up to top_k in stable order (as they appear in songs.json)
       - score=None
    """
    songs = load_songs()
    song_vectors = load_vectors()

    if len(songs) != song_vectors.shape[0]:
        raise ValueError(
            f"Mismatch: songs.json has {len(songs)} songs but song_vectors has "
            f"{song_vectors.shape[0]} vectors. Re-run embeddings.py after editing songs.json."
        )

    # Apply filters first
    filters = filters or {}
    filtered_indices = [i for i, s in enumerate(songs) if _matches_filters(s, filters)]

    if not filtered_indices:
        return []

    top_k = _ensure_top_k(top_k, len(filtered_indices))

    # Faceted-only mode
    q = (query or "").strip()
    if not q:
        return [
            {
                "score": None,
                **songs[i],
            }
            for i in filtered_indices[:top_k]
        ]

    # Semantic mode
    model = model or SentenceTransformer(MODEL_NAME)
    query_vec = model.encode([q], normalize_embeddings=True)[0]  # shape (d,)

    scores = song_vectors @ query_vec  # cosine sim if song vectors are normalized

    # Only score the filtered set
    scored = [(i, float(scores[i])) for i in filtered_indices]
    scored.sort(key=lambda x: x[1], reverse=True)
    scored = scored[:top_k]

    return [
        {
            "score": score,
            **songs[i],
        }
        for i, score in scored
    ]


if __name__ == "__main__":
    test_query = "soft dreamy songs for late night walking"
    filters = {"mood": ["dreamy"], "activity": ["walking"]}
    hits = semantic_search(test_query, top_k=5, filters=filters)

    print(f"Query: {test_query}")
    print(f"Filters: {filters}\n")
    for rank, h in enumerate(hits, start=1):
        sc = h["score"]
        sc_str = f"{sc:.3f}" if sc is not None else "None"
        print(f"{rank}. {h.get('title')} — {h.get('artist')} (score={sc_str})")