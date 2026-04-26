# Implementation Plan: Vibe Bot

## Overview

Add an interactive CLI mode to VibeMatch where users describe an activity or mood in natural language and receive a curated 5-song playlist with explanations. Implementation builds the `src/vibe_bot.py` agentic loop module, updates `src/main.py` with argparse flags, creates configuration templates, and adds comprehensive tests. All tasks use Python and build incrementally on the existing codebase.

## Tasks

- [x] 1. Add hypothesis to requirements.txt and create .env.example
  - [x] 1.1 Add `hypothesis` to `requirements.txt`
    - Append `hypothesis` to the existing requirements.txt file
    - _Requirements: 10.1_
  - [x] 1.2 Create `.env.example` configuration template
    - Create `.env.example` with a placeholder `ANTHROPIC_API_KEY=` entry
    - Include a comment explaining how to obtain the key at console.anthropic.com
    - Include a comment instructing the user to copy this file to `.env` and fill in their key
    - _Requirements: 10.3_

- [x] 2. Create core vibe_bot module with tool definition and helpers
  - [x] 2.1 Create `src/vibe_bot.py` with constants, imports, and the `get_search_songs_tool()` function
    - Define `MAX_ITERATIONS = 6` and `MODEL = "claude-haiku-4-5-20251001"`
    - Import `anthropic`, `json`, `logging`, `os`, `sys`, and `dotenv`
    - Implement `get_search_songs_tool()` returning the tool definition dict with all 16 genre enums and 15 mood enums from the catalog
    - Set up module-level logger with `logging.getLogger(__name__)`
    - _Requirements: 4.5, 4.6_
  - [x] 2.2 Implement `validate_api_key()` function
    - Call `load_dotenv()` to load `.env` file
    - Check `os.environ.get("ANTHROPIC_API_KEY")`
    - If missing or empty, print a descriptive error referencing `.env.example` and call `sys.exit(1)`
    - Return the key string on success
    - _Requirements: 2.1, 2.2, 2.3_
  - [x] 2.3 Implement `handle_search_songs()` function
    - Accept `tool_input` dict and `songs` list
    - Clamp energy to [0.0, 1.0] using `max(0.0, min(1.0, value))`
    - Construct `user_prefs` dict with genre, mood, and clamped energy
    - Call `recommend_songs(user_prefs, songs, k=5)` from `src/recommender.py`
    - Serialize top 5 results to JSON string with title, artist, genre, mood, energy, and score fields
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  - [x] 2.4 Implement `display_vibe_playlist()` function
    - Accept `vibe_input` string and `playlist_text` string
    - Print a header showing the original vibe input
    - Print the playlist text with clear visual formatting
    - _Requirements: 6.1, 6.2_

- [x] 3. Implement the agentic loop and interactive entry point
  - [x] 3.1 Implement `run_vibe_bot()` agentic loop function
    - Accept `vibe_input`, `songs`, `client`, and `debug` parameters
    - Build the system prompt instructing Claude to interpret vibes and build playlists
    - Initialize messages list with the user's vibe input
    - Loop: call `client.messages.create()` with model, system prompt, messages, and tool definition
    - On `tool_use` stop reason: extract tool name and input, call `handle_search_songs()` for `search_songs`, return error tool_result for unknown tools, append results to messages
    - On `end_turn` stop reason: extract and return the final text content
    - Enforce `MAX_ITERATIONS` cap — stop loop and return cap-reached message with any partial results
    - Log each API call iteration number at INFO level, log tool invocations with parameters at INFO level, log stop reasons at DEBUG level
    - If `debug` is True, log full request/response payloads at DEBUG level
    - Wrap loop in try/except for `anthropic.AuthenticationError`, `anthropic.RateLimitError`, `anthropic.APIStatusError`, and generic `Exception`
    - Return appropriate user-friendly error messages for each exception type
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.7, 5.1, 5.2, 5.3, 7.1, 7.2, 7.3, 7.4, 7.5, 8.1, 8.2, 8.3_
  - [x] 3.2 Implement `vibe_bot_interactive()` entry point function
    - Accept `debug` parameter (default False)
    - Call `validate_api_key()` to get the API key
    - Initialize `anthropic.Anthropic(api_key=key)` client
    - Call `load_songs("data/songs.csv")` to load the catalog
    - Prompt user for vibe input via `input()`
    - If input is empty, re-prompt with a helpful message
    - Call `run_vibe_bot()` with the vibe input, songs, client, and debug flag
    - Call `display_vibe_playlist()` with the result
    - If debug is True, set logging level to DEBUG
    - _Requirements: 3.1, 3.2, 3.3_

- [x] 4. Update CLI runner with argparse flags
  - [x] 4.1 Update `src/main.py` with `--vibe` and `--debug` argparse flags
    - Add `parse_args()` function using `argparse.ArgumentParser`
    - Add `--vibe` flag (store_true) to launch Vibe Bot mode
    - Add `--debug` flag (store_true) to enable debug logging
    - Update `main()` to call `parse_args()` and dispatch: if `--vibe`, import and call `vibe_bot_interactive(debug=args.debug)`; otherwise run existing demo mode
    - `--debug` without `--vibe` silently runs demo mode
    - Use deferred import of `vibe_bot` to avoid loading anthropic SDK in demo mode
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 5. Checkpoint — Verify core implementation
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Write unit tests for vibe_bot module
  - [x] 6.1 Create `tests/test_vibe_bot.py` with CLI argument parsing tests
    - Test `--vibe` flag launches vibe mode
    - Test no flags runs demo mode
    - Test `--debug --vibe` sets debug=True
    - Test `--debug` without `--vibe` runs demo mode
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  - [x] 6.2 Write unit tests for API key validation
    - Test missing key shows error and exits
    - Test empty key shows error and exits
    - Test valid key returns key string
    - Mock `load_dotenv` and `os.environ` to isolate tests
    - _Requirements: 2.2, 2.3_
  - [x] 6.3 Write unit tests for tool definition and search handler
    - Test tool definition contains all 16 genre enum values
    - Test tool definition contains all 15 mood enum values
    - Test unknown tool name returns error result
    - Test `handle_search_songs()` with real catalog data returns valid JSON with correct structure
    - _Requirements: 4.5, 4.6, 4.7, 9.1, 9.3_
  - [x] 6.4 Write unit tests for agentic loop behavior with mocked Claude client
    - Test iteration cap reached shows informative message
    - Test `AuthenticationError` shows API key message
    - Test `RateLimitError` suggests retry
    - Test generic `Exception` shows friendly message
    - Test `end_turn` stop reason extracts final text
    - Test `tool_use` stop reason triggers tool handler
    - Mock `anthropic.Anthropic` client with `unittest.mock.MagicMock`
    - _Requirements: 5.2, 8.1, 8.2, 8.3_
  - [x] 6.5 Write unit test for empty vibe input re-prompt
    - Mock `builtins.input` to return empty string then valid string
    - Verify re-prompt behavior
    - _Requirements: 3.2_

- [ ] 7. Write property-based tests for vibe_bot correctness properties
  - [x] 7.1 Write property test for energy clamping
    - **Property 1: Energy clamping produces bounded output**
    - Use `hypothesis` with `@given(st.floats())` to generate arbitrary float values
    - Assert clamped result is always in [0.0, 1.0]
    - Assert clamped result equals `max(0.0, min(1.0, value))`
    - Use `@settings(max_examples=100)`
    - **Validates: Requirements 9.4, 9.5**
  - [x] 7.2 Write property test for search songs tool result structure
    - **Property 2: Search songs tool returns valid structured results**
    - Use `hypothesis` to generate valid genre (sampled from 16 enums), mood (sampled from 15 enums), and energy (floats in [0.0, 1.0])
    - Call `handle_search_songs()` with generated inputs and real catalog
    - Assert result is valid JSON, deserializes to a list of at most 5 items
    - Assert each item has keys: title, artist, genre, mood, energy, score
    - Use `@settings(max_examples=100)`
    - **Validates: Requirements 4.3, 9.1, 9.3**
  - [x] 7.3 Write property test for agentic loop iteration cap
    - **Property 3: Agentic loop respects iteration cap**
    - Use a mocked Claude client that always returns `tool_use` stop reason
    - Use `hypothesis` to generate varying numbers of iterations
    - Assert the mocked client's `messages.create` is called at most `MAX_ITERATIONS` times
    - Use `@settings(max_examples=100)`
    - **Validates: Requirements 5.1**
  - [x] 7.4 Write property test for playlist display containing vibe input
    - **Property 4: Playlist display includes original vibe input**
    - Use `hypothesis` with `@given(st.text(min_size=1))` to generate arbitrary non-empty vibe strings
    - Capture stdout from `display_vibe_playlist()`
    - Assert the original vibe input string appears in the captured output
    - Use `@settings(max_examples=100)`
    - **Validates: Requirements 6.2**

- [x] 8. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- All Claude API interactions in tests use mocked clients — no real API calls during testing
- `hypothesis` is the only new dependency; `anthropic` and `python-dotenv` are already in requirements.txt
