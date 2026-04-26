"""
Vibe Bot — interactive CLI mode for VibeMatch.

Translates natural-language activity descriptions into curated 5-song
playlists using an agentic loop powered by the Claude API with tool use.
"""

import anthropic
import json
import logging
import os
import sys

from dotenv import load_dotenv

from src.recommender import load_songs, recommend_songs

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_ITERATIONS = 6
MODEL = "claude-haiku-4-5-20251001"

# ---------------------------------------------------------------------------
# Module-level logger
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool definition
# ---------------------------------------------------------------------------
def get_search_songs_tool() -> dict:
    """Return the search_songs tool definition for the Claude API."""
    return {
        "name": "search_songs",
        "description": (
            "Search the VibeMatch song catalog for songs matching a vibe. "
            "Returns the top 5 songs ranked by match score. "
            "You can call this multiple times with different parameters "
            "to explore the catalog."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "genre": {
                    "type": "string",
                    "description": "The genre to search for.",
                    "enum": [
                        "pop",
                        "lofi",
                        "rock",
                        "ambient",
                        "jazz",
                        "synthwave",
                        "indie pop",
                        "hip-hop",
                        "r&b",
                        "classical",
                        "metal",
                        "reggae",
                        "folk",
                        "edm",
                        "blues",
                        "soul",
                    ],
                },
                "mood": {
                    "type": "string",
                    "description": "The mood to search for.",
                    "enum": [
                        "happy",
                        "chill",
                        "intense",
                        "relaxed",
                        "moody",
                        "focused",
                        "confident",
                        "romantic",
                        "melancholic",
                        "aggressive",
                        "dreamy",
                        "sad",
                        "euphoric",
                        "nostalgic",
                        "tender",
                    ],
                },
                "energy": {
                    "type": "number",
                    "description": (
                        "Target energy level from 0.0 (calm) to 1.0 (intense)."
                    ),
                },
            },
            "required": ["genre", "mood", "energy"],
        },
    }


# ---------------------------------------------------------------------------
# API key validation
# ---------------------------------------------------------------------------
def validate_api_key() -> str:
    """Load .env and return the Anthropic API key, or exit with an error."""
    load_dotenv()
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print(
            "Error: ANTHROPIC_API_KEY not found.\n"
            "Copy .env.example to .env and add your key.\n"
            "Get one at https://console.anthropic.com"
        )
        sys.exit(1)
    return key


# ---------------------------------------------------------------------------
# Tool handler
# ---------------------------------------------------------------------------
def handle_search_songs(tool_input: dict, songs: list[dict]) -> str:
    """Execute search_songs tool call. Returns JSON string of top 5 results."""
    energy = max(0.0, min(1.0, tool_input.get("energy", 0.5)))
    user_prefs = {
        "genre": tool_input.get("genre", ""),
        "mood": tool_input.get("mood", ""),
        "energy": energy,
    }
    results = recommend_songs(user_prefs, songs, k=5)
    serialized = [
        {
            "title": song["title"],
            "artist": song["artist"],
            "genre": song["genre"],
            "mood": song["mood"],
            "energy": song["energy"],
            "score": score,
        }
        for song, score, _reasons in results
    ]
    return json.dumps(serialized)


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are VibeMatch DJ, a music recommendation assistant. The user will describe "
    "an activity, mood, or scenario. Your job is to:\n\n"
    "1. Interpret their vibe and decide on genre, mood, and energy parameters\n"
    "2. Use the search_songs tool to find matching songs from the catalog\n"
    "3. Review the results — if they don't feel right, search again with different parameters\n"
    "4. Once you have good results, write a playlist with exactly 5 songs\n\n"
    "Format your final response as a numbered playlist. For each song include:\n"
    "- Song title and artist\n"
    "- A brief explanation of why it fits the vibe\n\n"
    "Keep explanations concise and conversational. Do not include scores or technical details."
)


# ---------------------------------------------------------------------------
# Agentic loop
# ---------------------------------------------------------------------------
def run_vibe_bot(
    vibe_input: str,
    songs: list[dict],
    client: anthropic.Anthropic,
    debug: bool = False,
) -> str:
    """Run the agentic loop. Returns the final playlist text or an error/cap message."""
    tools = [get_search_songs_tool()]
    messages = [{"role": "user", "content": vibe_input}]

    if debug:
        logger.debug("System prompt: %s", SYSTEM_PROMPT)

    try:
        for iteration in range(1, MAX_ITERATIONS + 1):
            logger.info("API call iteration %d/%d", iteration, MAX_ITERATIONS)

            if debug:
                logger.debug(
                    "Request — messages: %s", json.dumps(messages, indent=2)
                )

            response = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=messages,
                tools=tools,
            )

            logger.debug("Stop reason: %s", response.stop_reason)

            if debug:
                logger.debug("Response — stop_reason: %s, content: %s",
                             response.stop_reason, response.content)

            # ---- end_turn: Claude is done, extract final text ----
            if response.stop_reason == "end_turn":
                text_parts = [
                    block.text
                    for block in response.content
                    if hasattr(block, "text")
                ]
                return "\n".join(text_parts) if text_parts else ""

            # ---- tool_use: process tool calls ----
            if response.stop_reason == "tool_use":
                # Append the full assistant message (contains tool_use blocks)
                messages.append({"role": "assistant", "content": response.content})

                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue

                    tool_name = block.name
                    tool_input = block.input

                    if tool_name == "search_songs":
                        logger.info(
                            "Tool call: search_songs(genre=%s, mood=%s, energy=%s)",
                            tool_input.get("genre"),
                            tool_input.get("mood"),
                            tool_input.get("energy"),
                        )
                        result_content = handle_search_songs(tool_input, songs)
                    else:
                        logger.warning("Unknown tool requested: %s", tool_name)
                        result_content = json.dumps(
                            {"error": f"Unknown tool: {tool_name}"}
                        )

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_content,
                        }
                    )

                messages.append({"role": "user", "content": tool_results})

        # Loop exhausted without end_turn
        logger.warning("Iteration cap reached (%d API calls)", MAX_ITERATIONS)
        return (
            f"Reached the iteration limit ({MAX_ITERATIONS} API calls). "
            "Here's what I found so far:"
        )

    except anthropic.AuthenticationError:
        logger.error("Authentication failed")
        return "Error: Invalid API key. Check your .env file."
    except anthropic.RateLimitError:
        logger.error("Rate limit exceeded")
        return "Error: API rate limit reached. Please try again in a few minutes."
    except anthropic.APIStatusError as e:
        logger.error("API error: %s", e)
        return f"Error: Claude API returned an error ({e.status_code}). Try again later."
    except Exception:
        logger.error("Unexpected error in agentic loop", exc_info=True)
        return "Something went wrong. Run with --debug for more details."


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Interactive entry point
# ---------------------------------------------------------------------------
def vibe_bot_interactive(debug: bool = False) -> None:
    """Main entry point. Validates API key, collects vibe, runs loop, displays result."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    key = validate_api_key()
    client = anthropic.Anthropic(api_key=key)
    songs = load_songs("data/songs.csv")

    vibe_input = input("\n🎵 Describe your vibe: ").strip()
    while not vibe_input:
        vibe_input = input("Please enter a vibe (e.g. 'chill study session'): ").strip()

    result = run_vibe_bot(vibe_input, songs, client, debug=debug)
    display_vibe_playlist(vibe_input, result)


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------
def display_vibe_playlist(vibe_input: str, playlist_text: str) -> None:
    """Print the final playlist with a header showing the original vibe."""
    print()
    print("=" * 60)
    print(f"  🎵 Playlist for: {vibe_input}")
    print("=" * 60)
    print()
    print(playlist_text)
    print()
    print("-" * 60)