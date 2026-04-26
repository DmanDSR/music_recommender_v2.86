# Project Context — VibeMatch Music Recommender

> Living document. Updated as the project changes, grows, and finishes tasks.
> Last updated: 2026-04-26 (Phases 1–3 complete, Phase 4 nearly complete — vibe_bot.py, CLI argparse flags, core checkpoint, unit tests, and property-based tests all complete; final checkpoint remaining)

---

## Project Overview

**Project name:** VibeMatch 1.0  
**Course:** CodePath AI110 — Spring 2026  
**Type:** Graded assignment — CLI-based music recommendation system  
**Language:** Python  
**Entry point:** `python -m src.main`

---

## Current Architecture

```
music_recommender_v2.86/
├── .env.example             # API key config template (created)
├── .kiro/
│   └── specs/vibe-bot/      # Spec: requirements, design, tasks
├── src/
│   ├── main.py              # CLI runner with --vibe and --debug argparse flags
│   ├── recommender.py       # Core recommendation logic
│   └── vibe_bot.py          # Vibe Bot module (core complete, checkpoint passed)
├── tests/
│   ├── test_recommender.py  # Unit tests for scoring pipeline + OOP classes
│   └── test_vibe_bot.py     # Unit + property tests for Vibe Bot (33 tests — CLI, API key, tool def, loop, input, PBT)
├── data/
│   └── songs.csv            # 19-song local catalog
├── requirements.txt         # anthropic, hypothesis, pytest, python-dotenv
├── README.md
├── model_card.md
├── context.md
├── reflection.md
└── User_Profile.md
```

### How It Works

1. `load_songs("data/songs.csv")` reads the 19-song catalog
2. For each of 3 hardcoded user profiles, `recommend_songs(user_prefs, songs, k=5)` scores every song
3. `score_song()` scores each song using three signals:
   - Genre match: +1.25 (binary)
   - Mood match: +1.5 (binary)
   - Energy proximity: `(1.0 - abs(song.energy - user.energy)) * 3.0` → 0 to +3.0
   - **Max score: 5.75**
4. Top 5 results printed to terminal with a visual score bar and match reasons

### Song Catalog (`data/songs.csv`)

19 songs. Key fields: `id, title, artist, genre, mood, energy, tempo_bpm, valence, danceability, acousticness`

**Available genres (16):** pop, lofi, rock, ambient, jazz, synthwave, indie pop, hip-hop, r&b, classical, metal, reggae, folk, edm, blues, soul  
**Available moods (15):** happy, chill, intense, relaxed, moody, focused, confident, romantic, melancholic, aggressive, dreamy, sad, euphoric, nostalgic, tender  
**Energy range:** 0.22 (Autumn Sonata / classical) to 0.96 (Iron Curtain / metal)

### Current Dependencies (`requirements.txt`)

```
anthropic
hypothesis
pytest
python-dotenv
```

Previously listed `pandas` and `streamlit` were removed — neither was used in the codebase. `hypothesis` was added for property-based testing of the Vibe Bot module. `pandas` may be re-added if the iTunes import stretch goal (Phase 5) is implemented.

---

## Known Issues

### Issue 1 — Duplicate `score_song()` bug (FIXED)

The duplicate `score_song()` definition (lines 97–104) that previously overrode the real implementation was already removed from `src/recommender.py` before the audit. Documentation has been updated to reflect this.

---

### Issue 2 — `Recommender` class is a non-functional stub (FIXED)

`src/recommender.py` contained a `Recommender` class with placeholder methods. `recommend()` returned `self.songs[:k]` with no scoring, and `explain_recommendation()` returned a hardcoded string. Tests passed by coincidence.

**Fix applied:** `Recommender.recommend()` now calls the real `score_song()` pipeline internally. `explain_recommendation()` returns actual score breakdowns. Tests rewritten with 9 cases that validate real scoring behavior — ranking flips for different profiles, perfect match scores 5.75, misses appear in explanations, and standalone functions are tested directly.

---

### Issue 3 — Scoring weights inconsistent between README and code (FIXED)

The README's algorithm table and mermaid data flow diagram previously showed old weights (genre +2.5, energy ×1.5). Updated to match the actual code (genre +1.25, energy ×3.0). Known Biases section also rewritten to reflect energy dominance instead of genre dominance.

---

### Issue 4 — Dead dependencies in `requirements.txt` (FIXED)

- `pandas` — was never imported; CSV loading uses the `csv` module. Removed. Will be re-added if iTunes import (Phase 5) is implemented.
- `streamlit` — was never imported anywhere. Removed.
- Added `anthropic` and `python-dotenv` for Vibe Bot.

---

### Issue 5 — `.gitignore` missing `.env` (FIXED)

Added `.env` to `.gitignore` to prevent accidental commits of API keys.

---

### Issue 6 — README has template placeholders and stale content (FIXED)

Filled in "Experiments You Tried" with weight-change experiment results and three-profile comparison. Filled in "Limitations and Risks" with catalog size, energy dominance, and mood rigidity. Replaced "Reflection" template with two paragraphs from model card insights. Removed the blank model card template (Section 7 onward).

---

### Issue 7 — No input validation in `load_songs()` (FIXED)

Added `FileNotFoundError` handling with a clear message pointing to `data/songs.csv`. Row-level `try/except` catches bad numeric values and skips the row with a warning instead of crashing. If zero valid songs are loaded, exits with an error message.

---

### Issue 8 — Fragile import pattern in `main.py` (FIXED)

Simplified to a single absolute import (`from src.recommender import ...`) matching the documented entry point `python -m src.main`. Removed the `try/except ModuleNotFoundError` workaround.

---

## Assignment Requirements

The feature expansion must satisfy all of the following:

### 1. Does Something Useful with AI
Examples from rubric: summarize text, retrieve information, plan a step-by-step task, help debug/classify/explain something.

### 2. At Least One Advanced AI Feature

| Feature | Description |
|---|---|
| **Retrieval-Augmented Generation (RAG)** | AI looks up information before answering |
| **Agentic Workflow** | AI can plan, act, and check its own work |
| Fine-Tuned / Specialized Model | Model trained for a specific task |
| Reliability / Testing System | Ways to measure or test AI performance |

The feature must be **fully integrated** into the main application logic — not a standalone script. The AI must actively use retrieved/processed data to formulate its response.

### 3. Runs Correctly and Reproducibly
Someone following the instructions should be able to run it without guessing.

### 4. Logging or Guardrails
Code must track what it does and handle errors safely.

### 5. Clear Setup Steps
Someone else should be able to run it without guessing what to install.

---

## Planned Feature: Vibe Bot

### Idea

An interactive mode where the user types what they want to do (e.g., "study for finals", "power workout", "lazy Sunday morning") and the system returns a curated 5-song playlist with a personalized explanation.

### Does It Meet the Requirements?

**Does something useful with AI** ✓  
Translates natural language activity descriptions into a curated playlist — clearly useful and AI-driven.

**Advanced AI Feature: Agentic Workflow** ✓ (best fit)
- Claude **plans** — interprets the user's vibe and decides what genre/mood/energy to search for
- Claude **acts** — calls a `search_songs` tool that runs the existing scoring pipeline
- Claude **checks** — can re-query with adjusted parameters if the first results aren't right, then writes the final playlist with explanations

**Fully integrated** ✓  
The `search_songs` tool calls the existing `recommend_songs()` function — the AI is driving the core system, not a side script.

**Logging/guardrails** ✓  
Python `logging` throughout, `MAX_ITERATIONS` cap to prevent runaway API spend, API key validation, error handling.

**Clear setup steps** ✓  
`.env.example` documents the `ANTHROPIC_API_KEY` requirement with step-by-step instructions.

---

## Vibe Bot Implementation Plan

### Files to Create / Modify

| Action | File | What Changes |
|--------|------|--------------|
| New module | `src/vibe_bot.py` | Full agentic loop with Claude tool use |
| Modify | `src/main.py` | Add `--vibe` and `--debug` argparse flags |
| Update | `requirements.txt` | Add `anthropic`, `python-dotenv`; remove `pandas`, `streamlit` |
| Create | `.env.example` | Document `ANTHROPIC_API_KEY` requirement |
| Update | `.gitignore` | Add `.env` entry |
| New tests | `tests/test_vibe_bot.py` | Mocked Claude tests + real catalog unit tests |

### Agentic Flow

```
User types: "power workout"
     |
vibe_bot_interactive()
     |
run_vibe_bot() starts agentic loop
     |
[API Call 1] → Claude receives user vibe
               Claude decides: high energy, euphoric, edm
               Claude returns: stop_reason="tool_use"
               tool_input={"genre":"edm","mood":"euphoric","energy":0.88}
     |
_handle_search_songs() called
   → recommend_songs({"genre":"edm","mood":"euphoric","energy":0.88}, songs, k=5)
   → score_song() called 19 times
   → ranked results returned as JSON
     |
[API Call 2] → Claude reads tool results
               Claude may re-query with different params (e.g., rock/intense)
               OR returns: stop_reason="end_turn" with final playlist text
     |
display_vibe_playlist() prints to terminal
```

### Model

`claude-haiku-4-5-20251001` — fast and cost-effective for a student project.

### Key Design Decisions

- **Tool use (function calling):** Claude calls `search_songs` as a tool, not just prompting it to suggest songs. This is what makes it agentic — Claude takes a real action, reads real results, and can adapt.
- **MAX_ITERATIONS = 6:** Hard cap on API calls per session. In practice, 2–3 calls are typical (one tool call, one final response). This guardrail prevents runaway spend.
- **Exact catalog values in tool description:** Claude must know the exact genre/mood strings (e.g., `"indie pop"` not `"indie-pop"`) because `score_song()` uses strict equality. Giving Claude accurate vocabulary directly improves playlist quality.
- **Existing `recommend_songs()` pipeline reused:** Vibe Bot does not bypass the scoring system — the AI layer sits on top of the existing algorithm.

### How to Run (After Implementation)

```bash
# Demo mode (no API key needed)
python -m src.main

# Vibe Bot mode
python -m src.main --vibe

# Vibe Bot with debug logging
python -m src.main --vibe --debug
```

### Test Vibes to Try

| Vibe input | Expected parameters |
|---|---|
| "I need to study for finals" | lofi or ambient / focused or chill / energy ~0.35–0.40 |
| "power workout, get me hyped" | edm or pop / euphoric or intense / energy ~0.88–0.93 |
| "lazy Sunday morning with coffee" | jazz or ambient / relaxed or chill / energy ~0.28–0.37 |
| "driving at night" | synthwave / moody / energy ~0.75 |

---

## Pre-Implementation Cleanup — Game Plan

Fix these before building Vibe Bot so the feature builds on a solid foundation.

### Phase 1 — Fix what's broken (do first)

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 1 | Clean up `requirements.txt` — remove `pandas`, `streamlit`; add `anthropic`, `python-dotenv` | `requirements.txt` | ✅ Done |
| 2 | Add `.env` to `.gitignore` | `.gitignore` | ✅ Done |
| 3 | Wire `Recommender` class to use real `score_song()` logic, or delete it and rewrite tests | `src/recommender.py`, `tests/test_recommender.py` | ✅ Done |

### Phase 2 — Fix what's misleading (before submission)

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 4 | Update README algorithm table and mermaid diagram to match actual weights (+1.25 genre, ×3.0 energy) | `README.md` | ✅ Done |
| 5 | Remove blank model card template from README (Section 7 onward) | `README.md` | ✅ Done |
| 6 | Fill in README "Experiments You Tried" and "Limitations and Risks" from `reflection.md` / `model_card.md` | `README.md` | ✅ Done |
| 7 | Update this document — mark Bug 1 as fixed, refresh task table | `Project_Context.md` | ✅ Done |

### Phase 3 — Harden (nice to have)

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 8 | Add error handling to `load_songs()` — catch `FileNotFoundError`, validate row data | `src/recommender.py` | ✅ Done |
| 9 | Simplify `main.py` import to absolute-only (`from src.recommender import ...`) | `src/main.py` | ✅ Done |

### Phase 4 — Build Vibe Bot (priority — must ship)

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 10 | Create `src/vibe_bot.py` — core module with constants, tool definition, API key validation, search handler, and display function | `src/vibe_bot.py` | ✅ Done (tasks 1–2 of spec) |
| 10a | Implement `get_search_songs_tool()` — tool definition with all 16 genre and 15 mood enums | `src/vibe_bot.py` | ✅ Done |
| 10b | Implement `validate_api_key()` — loads `.env`, checks key, exits with helpful error if missing | `src/vibe_bot.py` | ✅ Done |
| 10c | Implement `handle_search_songs()` — clamps energy, calls `recommend_songs()`, returns JSON | `src/vibe_bot.py` | ✅ Done |
| 10d | Implement `display_vibe_playlist()` — prints header with vibe input and formatted playlist | `src/vibe_bot.py` | ✅ Done |
| 10e | Implement `run_vibe_bot()` — agentic loop with iteration cap, error handling, logging | `src/vibe_bot.py` | ✅ Done |
| 10f | Implement `vibe_bot_interactive()` — entry point: key validation, input collection, loop dispatch | `src/vibe_bot.py` | ✅ Done |
| 11 | Update `src/main.py` with `--vibe` and `--debug` argparse flags | `src/main.py` | ✅ Done |
| 12 | Create `.env.example` | `.env.example` | ✅ Done |
| 12a | Add `hypothesis` to `requirements.txt` | `requirements.txt` | ✅ Done |
| — | **Checkpoint: verify core implementation (Task 5)** — all 9 tests pass, imports clean, catalog loads, demo mode runs | — | ✅ Done |
| 13 | Create `tests/test_vibe_bot.py` — unit tests for CLI args, API key, tool def, loop, input | `tests/test_vibe_bot.py` | ✅ Done (33 tests passing) |
| 13a | Property-based tests — energy clamping, result structure, iteration cap, display output | `tests/test_vibe_bot.py` | ✅ Done (4 properties, 100 examples each) |
| 14 | End-to-end test with real API key | — | ⬜ Not started |

### Phase 5 — Stretch Goal (only if time permits)

| # | Task | File(s) | Status |
|---|------|---------|--------|
| 15 | iTunes/Apple Music library import — read a real library export, map metadata to catalog schema, add `pandas` back as a dependency | `src/recommender.py`, `requirements.txt` | ⬜ Not started |

**Note:** `pandas` was removed from `requirements.txt` in Phase 1 because it's unused by the current 19-song CSV loader. If the iTunes import feature is implemented, `pandas` gets added back to handle cleaning, column mapping, and bulk operations on a larger catalog. Deadline is a few days out — this only happens if Phases 1–4 are done.

---

## What's Been Built So Far in `src/vibe_bot.py`

The core module is fully implemented — all six planned functions are complete. Here's the summary:

### Implemented Functions

| Function | What It Does | Status |
|----------|-------------|--------|
| `get_search_songs_tool()` | Returns the Claude tool definition dict with all 16 genre enums and 15 mood enums from the catalog | ✅ Complete |
| `validate_api_key()` | Loads `.env` via `python-dotenv`, checks `ANTHROPIC_API_KEY`, prints helpful error and exits if missing | ✅ Complete |
| `handle_search_songs()` | Clamps energy to [0.0, 1.0], builds `user_prefs` dict, calls `recommend_songs(prefs, songs, k=5)`, serializes top 5 results to JSON | ✅ Complete |
| `display_vibe_playlist()` | Prints a visual header with the original vibe input, the playlist text, and separator lines | ✅ Complete |
| `run_vibe_bot()` | The agentic loop — sends messages to Claude, handles tool_use/end_turn, enforces MAX_ITERATIONS cap, full error handling for auth/rate-limit/server/unexpected errors, structured logging at INFO and DEBUG levels | ✅ Complete |
| `vibe_bot_interactive()` | Entry point — validates API key, initializes Anthropic client, loads song catalog, prompts user for vibe input (re-prompts if empty), runs the agentic loop, displays the formatted playlist. Sets logging to DEBUG when `debug=True` | ✅ Complete |

### Constants and Setup

- `MAX_ITERATIONS = 6` — hard cap on API calls per session
- `MODEL = "claude-haiku-4-5-20251001"` — fast, cost-effective model
- `SYSTEM_PROMPT` — instructs Claude to interpret vibes, use the search_songs tool, and format a 5-song playlist
- Module-level logger via `logging.getLogger(__name__)`
- Imports: `anthropic`, `json`, `logging`, `os`, `sys`, `dotenv`, `recommender`

### What's Left

The `src/vibe_bot.py` module, CLI integration, and unit tests are all complete. Core checkpoint (Task 5) passed, and all 33 tests in `tests/test_vibe_bot.py` pass (Tasks 6 and 7 complete — unit tests and property-based tests). Remaining work:

1. **Task 8** — Final checkpoint: ensure all tests pass

### Property-Based Tests (Completed)

Four correctness properties are validated using `hypothesis` with 100 generated examples each:

| Property | Test Class | What It Validates |
|----------|-----------|-------------------|
| P1: Energy clamping bounded | `TestEnergyClamping` | For any float, clamped energy is in [0.0, 1.0] and equals `max(0.0, min(1.0, value))` |
| P2: Valid result structure | `TestSearchSongsToolResultStructure` | For any valid genre/mood/energy, `handle_search_songs()` returns valid JSON with ≤5 items, each with title/artist/genre/mood/energy/score |
| P3: Iteration cap respected | `TestAgenticLoopIterationCap` | For any number of tool_use responses, the loop calls the API at most `MAX_ITERATIONS` times |
| P4: Display contains vibe | `TestPlaylistDisplayContainsVibeInput` | For any non-empty string, `display_vibe_playlist()` output contains the original vibe input |

### CLI Integration (Completed)

`src/main.py` now uses `argparse` with two flags:

- `--vibe` — launches `vibe_bot_interactive()` from `src/vibe_bot.py`
- `--debug` — enables DEBUG-level logging (only effective with `--vibe`)
- No flags → runs the existing demo mode with 3 hardcoded profiles (unchanged)
- `--debug` without `--vibe` → silently runs demo mode

The `vibe_bot` import is deferred inside the `if args.vibe` branch so the `anthropic` SDK is not loaded in demo mode.
