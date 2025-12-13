import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterable, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer


# ----- Paths (relative to repo root) -----
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"

SONGS_PATH = DATA_DIR / "songs.json"
VECTORS_PATH = DATA_DIR / "song_vectors.npy"

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
    """
    Normalize a field to a list of strings.
    - list -> list[str]
    - str  -> [str]
    - None -> []
    """
    if x is None:
        return []
    if isinstance(x, list):
        return [str(v).strip() for v in x if str(v).strip()]
    if isinstance(x, str):
        s = x.strip()
        return [s] if s else []
    return [str(x).strip()] if str(x).strip() else []


def _matches_multi_select(song_val: Any, selected: List[str]) -> bool:
    """
    OR logic within a facet:
    - If selected is empty -> True (no constraint)
    - If song_val is list or str -> must share at least one selected tag
    """
    if not selected:
        return True
    song_tags = set(_as_list(song_val))
    selected_set = set([s.strip() for s in selected if s.strip()])
    return len(song_tags.intersection(selected_set)) > 0


def _matches_single(song_val: Any, selected: Optional[str]) -> bool:
    """
    Single-select facet (energy):
    - If selected is None -> True
    - If song_val is list or str -> must contain selected
    """
    if selected is None or selected == "":
        return True
    song_tags = set(_as_list(song_val))
    return selected in song_tags


def filter_song_indices(
    songs: List[Dict[str, Any]],
    filters: Optional[Dict[str, Any]] = None,
) -> List[int]:
    """
    AND logic across facets:
    mood/activity/genre: OR within each facet, AND across facets
    energy: single select
    """
    if not filters:
        return list(range(len(songs)))

    selected_mood = filters.get("mood", []) or []
    selected_activity = filters.get("activity", []) or []
    selected_genre = filters.get("genre", []) or []
    selected_energy = filters.get("energy", None)

    keep: List[int] = []
    for i, s in enumerate(songs):
        if not _matches_multi_select(s.get("mood"), selected_mood):
            continue
        if not _matches_multi_select(s.get("activity"), selected_activity):
            continue
        if not _matches_multi_select(s.get("genre"), selected_genre):
            continue
        if not _matches_single(s.get("energy"), selected_energy):
            continue
        keep.append(i)

    return keep


def get_facet_options(songs: Optional[List[Dict[str, Any]]] = None) -> Dict[str, List[str]]:
    """
    Build facet option lists directly from songs.json.
    """
    songs = songs or load_songs()

    moods = sorted({t for s in songs for t in _as_list(s.get("mood"))})
    activities = sorted({t for s in songs for t in _as_list(s.get("activity"))})
    genres = sorted({t for s in songs for t in _as_list(s.get("genre"))})
    energies = sorted({t for s in songs for t in _as_list(s.get("energy"))})

    return {
        "mood": moods,
        "activity": activities,
        "genre": genres,
        "energy": energies,  # e.g. ["high","low","medium"] depending on your data
    }


def semantic_search(
    query: Optional[str],
    top_k: int = 5,
    model: SentenceTransformer | None = None,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Hybrid behavior:
    - If query is provided -> rank by cosine similarity (within filtered subset)
    - If query is None/empty -> return filtered subset (no scores), truncated to top_k
    """
    songs = load_songs()

    # Filter first (Step 7 requirement)
    keep_idx = filter_song_indices(songs, filters=filters)
    if len(keep_idx) == 0:
        return []

    # Tag-only mode: no query => just browse filtered songs
    query_str = (query or "").strip()
    if not query_str:
        top_k = _ensure_top_k(top_k, len(keep_idx))
        return [songs[i] for i in keep_idx[:top_k]]

    # Semantic mode needs vectors
    song_vectors = load_vectors()
    if len(songs) != song_vectors.shape[0]:
        raise ValueError(
            f"Mismatch: songs.json has {len(songs)} songs but song_vectors has "
            f"{song_vectors.shape[0]} vectors. Re-run embeddings.py after editing songs.json."
        )

    top_k = _ensure_top_k(top_k, len(keep_idx))

    # Load model once (caller can pass a cached model)
    model = model or SentenceTransformer(MODEL_NAME)

    # Embed query (normalized so dot product becomes cosine similarity)
    query_vec = model.encode([query_str], normalize_embeddings=True)[0]  # (384,)

    # Compute similarity ONLY for the filtered subset
    subset_vecs = song_vectors[keep_idx]               # (m, 384)
    subset_scores = subset_vecs @ query_vec            # (m,)

    # Get top_k within subset
    subset_top = np.argsort(subset_scores)[::-1][:top_k]

    results: List[Dict[str, Any]] = []
    for j in subset_top:
        song_i = keep_idx[int(j)]
        results.append(
            {
                "score": float(subset_scores[int(j)]),
                **songs[song_i],
            }
        )

    return results


if __name__ == "__main__":
    test_query = "soft dreamy songs for late night walking"
    hits = semantic_search(test_query, top_k=5, filters=None)
    print(f"Query: {test_query}\n")
    for i, h in enumerate(hits, start=1):
        print(f"{i}. {h.get('title')} — {h.get('artist')}  (score={h['score']:.3f})")