import streamlit as st
from facets import collect_facet_options
from similarity import semantic_search, load_songs

st.set_page_config(page_title="Semantic Music Search", layout="wide")
songs = load_songs()
faceted_options = collect_facet_options(songs)

# ---- Color code scores (match strength) ----
def match_strength(score: float | None):
    """
    Returns (label, value, color) based on:
    - >= 0.45 : Very strong semantic match  -> green
    - 0.30-0.45: Good / relevant match      -> yellow
    - 0.20-0.30: Weak but related           -> orange
    - 0.00-0.20: Likely irrelevant          ->red
    - < 0.0   : Actively dissimilar         -> red
    """
    if score is None:
        return ("Match Strength:", "N/A", "#9ca3af")
    if score >= 0.45:
        return ("Match Strength:", f"{score:.3f}", "#2fb751")
    elif score >= 0.30:
        return ("Match Strength:", f"{score:.3f}", "#cca43f")
    elif score >= 0.20:
        return ("Match Strength:", f"{score:.3f}", "#c57834")
    else:
        return ("Match Strength:", f"{score:.3f}", "#ba3c3c")


# Two-column layout
filters_col, main_col = st.columns([1.25, 3], gap="large")

# Left: Filters ONLY
with filters_col:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    st.header("Filter by Tags")

    selected_moods = st.multiselect(
        "Mood",
        options=faceted_options["mood"],
        default=[],
    )

    selected_genres = st.multiselect(
        "Genre",
        options = faceted_options["genre"],
        default = [],
    )

    selected_activities = st.multiselect(
        "Activity",
        options = faceted_options["activity"],
        default = [],
    )

    selected_energy = st.selectbox(
        "Energy",
        options = ["Any", "low", "medium", "high"],
        index = 0,
    )

filters = {
    "mood": selected_moods,
    "genre": selected_genres,
    "activity": selected_activities,
    "energy": None if selected_energy == "Any" else selected_energy,
}

has_any_filter = any(v for v in filters.values() if v)
has_query = False  # set below after query input


# Right: Main content ONLY (title, text, search, results)
with main_col:
    st.title("Jaime's Recs 🎧")
    st.write(
        "I pulled some songs from my Spotify Library 📚. On this site, you can get my song recs 🎵🩶! Use your own words to get a Top 5 list with the songs from my library that match your prompt. You can also use the filters to narrow down your search or just use filters to browse the library, but that won't give you a match."
    )

    st.caption("Use your own words to get my recs! Press enter and see the song matches!")
    query = st.text_input(
        label = "",
        placeholder="e.g. Dreamy late night walking music",
    )

    has_query = bool((query or "").strip())

    # Count songs in scope (facets only)
    if has_any_filter:
        scoped = semantic_search(query=None, top_k=100_000, filters=filters)
        st.caption(f"Songs in scope: {len(scoped)}")

    # Mode A: semantic search (query exists)
    if has_query:
        results = semantic_search(query=query, top_k=5, filters=filters)

        st.subheader("Top Matches")

        if not results:
            st.info("No songs matched those filters / query. Try loosening filters or changing wording.")
        else:
            for i, r in enumerate(results, start=1):
                title = r.get("title", "Untitled")
                artist = r.get("artist", "Unknown")
                desc = (r.get("description") or "").strip()
                score = r.get("score")

                col_left, col_right = st.columns([4, 1])

                with col_left:
                    st.markdown(
                        f"""
                        <div style="font-size: 1.35rem; font-weight: 700; line-height: 1.2;">
                            {i}. {title} — {artist}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with col_right:
                    label, value, color = match_strength(score)
                    st.markdown(
                        f"""
                        <div style="
                            text-align: right;
                            font-size: 0.95rem;
                            font-weight: 400;
                            white-space: nowrap;
                        ">
                            <span style="color: #9ca3af;">{label}</span>
                            <span style="color: {color}; margin-left: 0.25rem;">
                                {value}
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                if desc:
                    st.write(desc)
                else:
                    st.caption("No description provided.")

                with st.expander(
                    "If you're wondering why this song is here... this is how I how I tagged it.",
                    expanded=False,
                ):
                    mood_val = r.get("mood", [])
                    mood_str = ", ".join(mood_val) if isinstance(mood_val, list) else str(mood_val)

                    activity_val = r.get("activity", [])
                    activity_str = ", ".join(activity_val) if isinstance(activity_val, list) else str(activity_val)

                    genre_val = r.get("genre", [])
                    genre_str = ", ".join(genre_val) if isinstance(genre_val, list) else str(genre_val)

                    energy_str = str(r.get("energy", ""))

                    vibes = r.get("vibe_tags", [])
                    vibe_str = ", ".join(vibes) if isinstance(vibes, list) else str(vibes)

                    st.write(f"**Mood:** {mood_str}")
                    st.write(f"**Activity:** {activity_str}")
                    st.write(f"**Genre:** {genre_str}")
                    st.write(f"**Energy:** {energy_str}")
                    if vibe_str and vibe_str != "None":
                        st.write(f"**Vibe tags:** {vibe_str}")

                st.divider()

    # Mode B: faceted-only browse (no query, filters exist)
    elif has_any_filter:
        st.subheader("Tag-Only Results")

        browse_k = st.slider("How many results to show", min_value=5, max_value=50, value=15, step=5)
        results = semantic_search(query=None, top_k=browse_k, filters=filters)

        if not results:
            st.info("No songs matched those filters. Try loosening filters.")
        else:
            for i, r in enumerate(results, start=1):
                title = r.get("title", "Untitled")
                artist = r.get("artist", "Unknown")
                desc = (r.get("description") or "").strip()

                st.markdown(
                    f"""
                    <div style="font-size: 1.35rem; font-weight: 700; line-height: 1.2;">
                        {i}. {title} — {artist}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if desc:
                    st.write(desc)
                else:
                    st.caption("No description provided.")

                with st.expander(
                    "If you're wondering why this song is here... this is how I how I tagged it.",
                    expanded=False,
                ):
                    mood_val = r.get("mood", [])
                    mood_str = ", ".join(mood_val) if isinstance(mood_val, list) else str(mood_val)

                    activity_val = r.get("activity", [])
                    activity_str = ", ".join(activity_val) if isinstance(activity_val, list) else str(activity_val)

                    genre_val = r.get("genre", [])
                    genre_str = ", ".join(genre_val) if isinstance(genre_val, list) else str(genre_val)

                    energy_str = str(r.get("energy", ""))

                    vibes = r.get("vibe_tags", [])
                    vibe_str = ", ".join(vibes) if isinstance(vibes, list) else str(vibes)

                    st.write(f"**Mood:** {mood_str}")
                    st.write(f"**Activity:** {activity_str}")
                    st.write(f"**Genre:** {genre_str}")
                    st.write(f"**Energy:** {energy_str}")
                    if vibe_str and vibe_str != "None":
                        st.write(f"**Vibe tags:** {vibe_str}")

                st.divider()

    else:
        st.caption("Start by typing a search or selecting filters.")