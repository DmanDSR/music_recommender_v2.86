# Requirements Document

## Introduction

Vibe Bot is an interactive CLI mode for the VibeMatch Music Recommender that translates natural-language activity descriptions (e.g., "study for finals", "power workout") into curated 5-song playlists with personalized explanations. It uses an agentic workflow powered by the Claude API, where Claude interprets the user's vibe, calls a `search_songs` tool backed by the existing `recommend_songs()` scoring pipeline, reads results, optionally re-queries with adjusted parameters, and produces a final playlist. The feature adds `--vibe` and `--debug` CLI flags, enforces a hard cap on API iterations, and includes logging, error handling, and API key validation.

## Glossary

- **Vibe_Bot**: The interactive CLI module (`src/vibe_bot.py`) that orchestrates the agentic loop between the user, the Claude API, and the song catalog.
- **Claude_API**: The Anthropic Claude language model API (model `claude-haiku-4-5-20251001`) used to interpret user vibes and generate playlist recommendations via tool use.
- **Search_Songs_Tool**: A tool definition exposed to the Claude API that wraps the existing `recommend_songs()` function, allowing Claude to query the song catalog with genre, mood, and energy parameters.
- **Scoring_Pipeline**: The existing `recommend_songs()` and `score_song()` functions in `src/recommender.py` that score and rank songs against user preference parameters.
- **Agentic_Loop**: The iterative cycle where the Vibe_Bot sends messages to the Claude_API, processes tool-use responses by calling the Search_Songs_Tool, feeds results back, and repeats until Claude produces a final text response or the iteration cap is reached.
- **Song_Catalog**: The 19-song CSV dataset (`data/songs.csv`) containing song metadata including genre, mood, energy, tempo, valence, danceability, and acousticness.
- **Vibe_Input**: A free-form natural-language string provided by the user describing an activity, mood, or scenario (e.g., "lazy Sunday morning with coffee").
- **Playlist_Output**: The final formatted text response containing up to 5 recommended songs with explanations, displayed to the user in the terminal.
- **MAX_ITERATIONS**: A hard cap constant (value: 6) limiting the number of Claude API calls per Vibe_Bot session to prevent runaway API spend.
- **CLI_Runner**: The `src/main.py` module that parses command-line arguments and dispatches to either the demo mode or the Vibe_Bot interactive mode.

## Requirements

### Requirement 1: CLI Entry Point with Vibe and Debug Flags

**User Story:** As a user, I want to launch the Vibe Bot from the command line using a `--vibe` flag, so that I can access the interactive playlist mode without modifying code.

#### Acceptance Criteria

1. WHEN the `--vibe` flag is provided, THE CLI_Runner SHALL launch the Vibe_Bot interactive mode.
2. WHEN no flags are provided, THE CLI_Runner SHALL run the existing demo mode with three hardcoded user profiles.
3. WHEN the `--debug` flag is provided alongside `--vibe`, THE CLI_Runner SHALL set the logging level to DEBUG for all Vibe_Bot modules.
4. WHEN the `--debug` flag is provided without `--vibe`, THE CLI_Runner SHALL ignore the `--debug` flag and run the demo mode.

### Requirement 2: API Key Validation

**User Story:** As a user, I want the system to validate that my Anthropic API key is configured before starting, so that I get a clear error message instead of a cryptic failure.

#### Acceptance Criteria

1. WHEN the Vibe_Bot starts, THE Vibe_Bot SHALL load environment variables from a `.env` file using `python-dotenv`.
2. IF the `ANTHROPIC_API_KEY` environment variable is missing or empty, THEN THE Vibe_Bot SHALL display a descriptive error message referencing `.env.example` and exit without making API calls.
3. WHEN a valid `ANTHROPIC_API_KEY` is present, THE Vibe_Bot SHALL initialize the Anthropic client with the provided key.

### Requirement 3: User Vibe Input Collection

**User Story:** As a user, I want to type a free-form description of my current activity or mood, so that the system can generate a matching playlist.

#### Acceptance Criteria

1. WHEN the Vibe_Bot interactive mode starts, THE Vibe_Bot SHALL prompt the user to enter a Vibe_Input string.
2. IF the user provides an empty Vibe_Input, THEN THE Vibe_Bot SHALL re-prompt the user with a helpful message.
3. WHEN the user provides a non-empty Vibe_Input, THE Vibe_Bot SHALL pass the Vibe_Input to the Agentic_Loop for processing.

### Requirement 4: Agentic Loop with Claude Tool Use

**User Story:** As a user, I want Claude to interpret my vibe, search the song catalog, and optionally refine its search, so that I get the best possible playlist for my activity.

#### Acceptance Criteria

1. WHEN the Agentic_Loop starts, THE Vibe_Bot SHALL send the Vibe_Input to the Claude_API with the Search_Songs_Tool definition and a system prompt instructing Claude to interpret vibes and build playlists.
2. WHEN the Claude_API responds with a `tool_use` stop reason, THE Vibe_Bot SHALL extract the tool name and input parameters from the response.
3. WHEN the Claude_API requests the `search_songs` tool, THE Vibe_Bot SHALL call the Scoring_Pipeline with the genre, mood, and energy parameters provided by Claude and return the top 5 results as a JSON-formatted tool result.
4. WHEN the Claude_API responds with an `end_turn` stop reason, THE Vibe_Bot SHALL extract the final text content as the Playlist_Output.
5. THE Vibe_Bot SHALL include the exact Song_Catalog genre values (pop, lofi, rock, ambient, jazz, synthwave, indie pop, hip-hop, r&b, classical, metal, reggae, folk, edm, blues, soul) in the Search_Songs_Tool definition.
6. THE Vibe_Bot SHALL include the exact Song_Catalog mood values (happy, chill, intense, relaxed, moody, focused, confident, romantic, melancholic, aggressive, dreamy, sad, euphoric, nostalgic, tender) in the Search_Songs_Tool definition.
7. WHEN the Claude_API requests a tool other than `search_songs`, THE Vibe_Bot SHALL return an error result indicating the tool is not recognized.

### Requirement 5: Iteration Cap Guardrail

**User Story:** As a developer, I want a hard cap on API calls per session, so that the system cannot run up excessive API costs from a single user interaction.

#### Acceptance Criteria

1. THE Vibe_Bot SHALL enforce a MAX_ITERATIONS limit of 6 API calls per Agentic_Loop session.
2. WHEN the Agentic_Loop reaches the MAX_ITERATIONS limit without receiving an `end_turn` response, THE Vibe_Bot SHALL stop the loop and display a message informing the user that the iteration limit was reached.
3. WHEN the Agentic_Loop reaches the MAX_ITERATIONS limit, THE Vibe_Bot SHALL display any partial results collected during the session.

### Requirement 6: Playlist Display

**User Story:** As a user, I want the final playlist displayed in a clear, readable format in my terminal, so that I can see the recommended songs and understand why they were chosen.

#### Acceptance Criteria

1. WHEN the Agentic_Loop produces a Playlist_Output, THE Vibe_Bot SHALL display the Playlist_Output text in the terminal with clear visual formatting.
2. THE Vibe_Bot SHALL display a header indicating the user's original Vibe_Input before the playlist.

### Requirement 7: Logging

**User Story:** As a developer, I want structured logging throughout the Vibe Bot workflow, so that I can debug issues and monitor the agentic loop behavior.

#### Acceptance Criteria

1. THE Vibe_Bot SHALL log each Claude_API call with the iteration number at INFO level.
2. THE Vibe_Bot SHALL log each Search_Songs_Tool invocation with the parameters received from Claude at INFO level.
3. THE Vibe_Bot SHALL log the stop reason of each Claude_API response at DEBUG level.
4. WHEN the `--debug` flag is active, THE Vibe_Bot SHALL log the full Claude_API request and response payloads at DEBUG level.
5. IF an error occurs during the Agentic_Loop, THEN THE Vibe_Bot SHALL log the error with full context at ERROR level.

### Requirement 8: Error Handling

**User Story:** As a user, I want the system to handle API errors and unexpected failures gracefully, so that I see a helpful message instead of a stack trace.

#### Acceptance Criteria

1. IF the Claude_API returns an authentication error, THEN THE Vibe_Bot SHALL display a message indicating the API key is invalid and exit gracefully.
2. IF the Claude_API returns a rate-limit or server error, THEN THE Vibe_Bot SHALL display a message describing the error and suggest the user try again later.
3. IF an unexpected exception occurs during the Agentic_Loop, THEN THE Vibe_Bot SHALL log the exception at ERROR level and display a user-friendly error message.

### Requirement 9: Search Songs Tool Integration with Scoring Pipeline

**User Story:** As a developer, I want the search_songs tool to use the existing scoring pipeline, so that the AI-driven recommendations are consistent with the core algorithm.

#### Acceptance Criteria

1. WHEN the Search_Songs_Tool is invoked, THE Vibe_Bot SHALL construct a user preferences dictionary with genre, mood, and energy keys from the tool input parameters.
2. WHEN the Search_Songs_Tool is invoked, THE Vibe_Bot SHALL call `recommend_songs()` from `src/recommender.py` with the constructed preferences, the full Song_Catalog, and `k=5`.
3. THE Search_Songs_Tool SHALL return results as a JSON string containing each song's title, artist, genre, mood, energy, and match score.
4. WHEN the tool input contains an energy value, THE Search_Songs_Tool SHALL validate that the energy value is a float between 0.0 and 1.0.
5. IF the tool input contains an energy value outside the 0.0 to 1.0 range, THEN THE Search_Songs_Tool SHALL clamp the value to the nearest bound (0.0 or 1.0).

### Requirement 10: Dependency and Configuration Management

**User Story:** As a developer setting up the project, I want clear dependency declarations and configuration templates, so that I can get the project running without guessing.

#### Acceptance Criteria

1. THE requirements.txt SHALL include `anthropic` and `python-dotenv` as dependencies. *(Already done)*
2. THE requirements.txt SHALL NOT include `streamlit` or `pandas` as dependencies (neither is used by the current codebase). *(Already done)*
3. THE .env.example file SHALL contain a placeholder entry for `ANTHROPIC_API_KEY` with a comment explaining how to obtain the key.
4. THE .gitignore file SHALL include an entry for `.env` to prevent accidental commits of API keys. *(Already done)*
