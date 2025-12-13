# app/facets.py
from __future__ import annotations
from typing import Any, Dict, List, Optional

def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        v = value.strip()
        return [v] if v else []
    return [str(value).strip()]

def collect_facet_options(songs: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Scan songs.json and return sorted unique options for each facet."""
    moods, activities, energies, genres = set(), set(), set(), set()

    for s in songs:
        for m in _as_list(s.get("mood")):
            moods.add(m)
        for a in _as_list(s.get("activity")):
            activities.add(a)
        e = str(s.get("energy", "")).strip()
        if e:
            energies.add(e)
        for g in _as_list(s.get("genre")):
            genres.add(g)

    return {
        "mood": sorted(moods),
        "activity": sorted(activities),
        "energy": sorted(energies),
        "genre": sorted(genres),
    }

def _matches_any(song_values: List[str], selected: List[str]) -> bool:
    """True if song has at least one of the selected values (OR)."""
    if not selected:
        return True
    sv = set(song_values)
    return any(x in sv for x in selected)

def filter_songs(
    songs: List[Dict[str, Any]],
    mood: Optional[List[str]] = None,
    activity: Optional[List[str]] = None,
    energy: Optional[str] = None,
    genre: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Filter songs by selected facets. mood/activity/genre use OR within facet."""
    mood = mood or []
    activity = activity or []
    genre = genre or []
    energy = (energy or "").strip()

    filtered = []
    for s in songs:
        s_mood = _as_list(s.get("mood"))
        s_activity = _as_list(s.get("activity"))
        s_genre = _as_list(s.get("genre"))
        s_energy = str(s.get("energy", "")).strip()

        if not _matches_any(s_mood, mood):
            continue
        if not _matches_any(s_activity, activity):
            continue
        if not _matches_any(s_genre, genre):
            continue
        if energy and s_energy != energy:
            continue

        filtered.append(s)

    return filtered