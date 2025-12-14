# Metadata Schema: songs.json

This project uses a structured, faceted metadata schema for each song entry the file `songs.json`.  
The schema supports **faceted browsing** (filters) and **semantic search/retrieval**  using embeddings from both `description` and facets (`mood`, `activity`, `genre`, `vibe tags` only). All tagging and description is based on my own perspective - the fun part is that people interacting with the webpage will receive song recommendations based on how their natural language matched my own categorization and description of songs I like.

---

## Song Object

Each song is one JSON object with the following required fields:

#### `title` (string)
- The song title.
- Example: `"Vanish Into You"`

#### `artist` (string or array of strings, if multiple)
- Primary artist name(s).
- Use a **string** for one artist, or an **array** for collaborations.
- Examples:
  - `"Lady Gaga"`
  - `["ROSALÍA", "Yahritza y Su Esencia"]`

#### `mood` (array of strings)
- Emotion/feeling descriptors (faceted).
- Always an array, even if there is only one mood.
- Full list: `calm`, `melancholic`, `dreamy`, `uplifting`, `nostalgic`, `energetic`, `warm`, `gritty`, `frustrated`
- Examples: 
  - `["dreamy", "melancholic"]`
  - `["uplifting"]`

#### `activity` (array of strings)
- Common listening contexts (faceted).
- Always an array.
- Full list: `studying`, `walking`, `cooking`, `relaxing`, `late night`, `working out`, `commuting`, `crying`, `reflecting`, `driving`, `daydreaming`, `venting`
- Examples:
  - `["driving", "late night", "reflecting"]`
  - `["cooking"]`

#### `energy` (string and not included in embedding)
- One of (single value):
  - `"low"`
  - `"medium"`
  - `"high"`

#### `genre` (array of strings)
- Broad musical categories (faceted).
- Always an array.
- Full list: `pop`, `indie`, `alternative`, `electronic`, `r&b`, `rock`, `folk`, `country`, `mariachi`, `flamenco`, `classical`, `jazz`, `soul`
- Examples:
  - `["pop"]`
  - `["rock", "alternative"]`

#### `vibe_tags` (array of strings)
- Extra descriptors that are more nuanced to complement context/vibe.
- Always an array.
- Full list: `cinematic`, `intimate`, `expansive`, `airy`, `dark`, `warm`, `hazy`, `moody`, `lo-fi`, `synthy`, acoustic, `layered`, `minimal`, `textured`, `ethereal`, `soft vocals`, `distorted vocals`, `melodic`, `rhythmic`, `raw`, `futuristic`, `hypnotic`, `retro`, `chaotic`
- Examples:
  - `["synthy", "layered", "cinematic"]`
  - `["acoustic", "raw", "retro"]`

#### `description` (string)
- A couple of sentences to describe the song.
- This is the **primary text used for embeddings**.
- Example:
  - `"Sparkly pop production that feels hopeful and endless. Like chasing light when it’s about to fade."`

---

## Example Entry

```json
{
  "title": "Vanish Into You",
  "artist": "Lady Gaga",
  "mood": ["uplifting", "energetic", "dreamy", "warm"],
  "activity": ["driving", "working out", "late night", "daydreaming", "cooking"],
  "energy": "high",
  "genre": ["pop"],
  "vibe_tags": ["synthy", "futuristic", "expansive", "rhythmic", "layered"],
  "description": "Raw pop with big hooks and a floaty rush. Feels like disappearing into the lights and forgetting your own thoughts."
}