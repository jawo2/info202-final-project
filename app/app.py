import streamlit as st
from similarity import semantic_search

st.set_page_config(page_title="Semantic Music Search", layout="wide")


# ---- Color code scores (match strength) ----
def match_strength(score: float | None):
    """
    Returns (label, value, color) based on:
    - >= 0.45 : Very strong semantic match  -> green
    - 0.30-0.45: Good / relevant match      -> yellow
    - 0.20-0.30: Weak but related           -> orange
    - 0.00-0.20: Likely irrelevant          -> red
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


# =========================
# LAYOUT: Filters (left) + Main content (right)
# =========================
left, main = st.columns([1, 3], gap="large")

with left:
    st.markdown("## Filter by Tags")

    selected_moods = st.multiselect(
        "Mood",
        options=[
            "calm",
            "melancholic",
            "dreamy",
            "uplifting",
            "nostalgic",
            "energetic",
            "warm",
            "dark",
            "gritty",
        ],
        default=[],
    )

    selected_genres = st.multiselect(
        "Genre",
        options=["pop", "indie", "alternative", "electronic", "R&B", "hip-hop", "rock"],
        default=[],
    )

    selected_activities = st.multiselect(
        "Activity",
        options=[
            "studying",
            "walking",
            "cooking",
            "relaxing",
            "late night",
            "working out",
            "commuting",
            "driving",
            "reflecting",
            "crying",
        ],
        default=[],
    )

    selected_energy = st.selectbox(
        "Energy",
        options=["Any", "low", "medium", "high"],
        index=0,
    )


with main:
    st.title("Jaime's Recs 🎧")
    st.write(
        "I made a pool of songs I think you'd like 🎵🩶! You can do an open search to get a Top 5 of matches and use filters if you want. Or you can just use filters to browse the song pool."
    )

    query = st.text_input(
        "Use your own words to get my recs! Press enter and see the song matches!",
        placeholder="e.g. Dreamy late night walking music",
    )

    st.caption("Tip: Enter a search query, select filters, or both.")

    filters = {
        "mood": selected_moods,
        "genre": selected_genres,
        "activity": selected_activities,
        "energy": None if selected_energy == "Any" else selected_energy,
    }

    has_any_filter = any(v for v in filters.values() if v)
    has_query = bool((query or "").strip())

    # Count songs in scope (facets only)
    if has_any_filter:
        scoped = semantic_search(query=None, top_k=100_000, filters=filters)
        st.caption(f"Songs in scope: {len(scoped)}")

    # -------------------------
    # Mode A: semantic search (query exists)
    # -------------------------
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

                # Header row: title/artist (left) + match strength (right)
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

                # Description (visible)
                if desc:
                    st.write(desc)
                else:
                    st.caption("No description provided.")

                # Collapsible metadata
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

    # -------------------------
    # Mode B: faceted-only browse (no query, filters exist)
    # -------------------------
    elif has_any_filter:
        st.subheader("Tag-Only Results")

        browse_k = st.slider("How many results to show", min_value=5, max_value=50, value=15, step=5)
        results = semantic_search(query=None, top_k=browse_k, filters=filters)

        if not results:
            st.info("No songs matched those filters. Try loosening filters.")
        else:
            # Same format as Top Matches, just NO match strength on the right.
            for i, r in enumerate(results, start=1):
                title = r.get("title", "Untitled")
                artist = r.get("artist", "Unknown")
                desc = (r.get("description") or "").strip()

                # Header row: title/artist only (no match strength)
                st.markdown(
                    f"""
                    <div style="font-size: 1.35rem; font-weight: 700; line-height: 1.2;">
                        {i}. {title} — {artist}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Description (visible)
                if desc:
                    st.write(desc)
                else:
                    st.caption("No description provided.")

                # Collapsible metadata (same as Top Matches)
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

    # -------------------------
    # Mode C: nothing selected yet
    # -------------------------
    else:
        st.caption("Start by typing a search or selecting filters.")