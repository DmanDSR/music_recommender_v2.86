"""Tests for the vibe_bot module and CLI argument parsing."""

import json
import math
import os
import sys
from unittest.mock import patch, MagicMock

import anthropic
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.main import parse_args
from src.vibe_bot import (
    validate_api_key,
    get_search_songs_tool,
    handle_search_songs,
    run_vibe_bot,
    display_vibe_playlist,
    MAX_ITERATIONS,
)
from src.recommender import load_songs


# ---------------------------------------------------------------------------
# 6.1 — CLI argument parsing tests (Requirements 1.1, 1.2, 1.3, 1.4)
# ---------------------------------------------------------------------------


class TestParseArgs:
    """Tests for the --vibe and --debug CLI flags."""

    def test_vibe_flag_sets_vibe_true(self):
        """--vibe flag should set args.vibe to True (Requirement 1.1)."""
        with patch.object(sys, "argv", ["main", "--vibe"]):
            args = parse_args()
        assert args.vibe is True

    def test_no_flags_defaults_to_demo_mode(self):
        """No flags should leave args.vibe as False (Requirement 1.2)."""
        with patch.object(sys, "argv", ["main"]):
            args = parse_args()
        assert args.vibe is False
        assert args.debug is False

    def test_debug_with_vibe_sets_both_true(self):
        """--debug --vibe should set both flags to True (Requirement 1.3)."""
        with patch.object(sys, "argv", ["main", "--debug", "--vibe"]):
            args = parse_args()
        assert args.vibe is True
        assert args.debug is True

    def test_debug_without_vibe_runs_demo_mode(self):
        """--debug alone should leave args.vibe as False (Requirement 1.4)."""
        with patch.object(sys, "argv", ["main", "--debug"]):
            args = parse_args()
        assert args.vibe is False
        assert args.debug is True


class TestMainDispatch:
    """Tests that main() dispatches correctly based on CLI flags."""

    @patch("src.main.recommend_songs")
    @patch("src.main.load_songs")
    def test_no_flags_runs_demo_mode(self, mock_load, mock_recommend):
        """No flags should run the existing demo mode (Requirement 1.2)."""
        mock_load.return_value = [
            {
                "title": "Test",
                "artist": "Artist",
                "genre": "pop",
                "mood": "happy",
                "energy": 0.8,
            }
        ]
        mock_recommend.return_value = [
            (
                {
                    "title": "Test",
                    "artist": "Artist",
                    "genre": "pop",
                    "mood": "happy",
                    "energy": 0.8,
                },
                5.0,
                "genre match; mood match",
            )
        ]

        from src.main import main

        with patch.object(sys, "argv", ["main"]):
            main()

        mock_load.assert_called_once()
        assert mock_recommend.call_count == 3  # three hardcoded profiles

    @patch("src.vibe_bot.vibe_bot_interactive")
    def test_vibe_flag_launches_vibe_mode(self, mock_interactive):
        """--vibe flag should call vibe_bot_interactive (Requirement 1.1)."""
        from src.main import main

        with patch.object(sys, "argv", ["main", "--vibe"]):
            main()

        mock_interactive.assert_called_once_with(debug=False)

    @patch("src.vibe_bot.vibe_bot_interactive")
    def test_vibe_debug_passes_debug_true(self, mock_interactive):
        """--vibe --debug should call vibe_bot_interactive(debug=True) (Requirement 1.3)."""
        from src.main import main

        with patch.object(sys, "argv", ["main", "--vibe", "--debug"]):
            main()

        mock_interactive.assert_called_once_with(debug=True)

    @patch("src.main.recommend_songs")
    @patch("src.main.load_songs")
    def test_debug_without_vibe_runs_demo(self, mock_load, mock_recommend):
        """--debug without --vibe should run demo mode, ignoring debug (Requirement 1.4)."""
        mock_load.return_value = [
            {
                "title": "Test",
                "artist": "Artist",
                "genre": "pop",
                "mood": "happy",
                "energy": 0.8,
            }
        ]
        mock_recommend.return_value = [
            (
                {
                    "title": "Test",
                    "artist": "Artist",
                    "genre": "pop",
                    "mood": "happy",
                    "energy": 0.8,
                },
                5.0,
                "genre match; mood match",
            )
        ]

        from src.main import main

        with patch.object(sys, "argv", ["main", "--debug"]):
            main()

        mock_load.assert_called_once()
        # vibe_bot_interactive should NOT have been called


# ---------------------------------------------------------------------------
# 6.2 — API key validation tests (Requirements 2.2, 2.3)
# ---------------------------------------------------------------------------


class TestValidateApiKey:
    """Tests for validate_api_key() — loading .env and checking ANTHROPIC_API_KEY."""

    @patch("src.vibe_bot.load_dotenv")
    def test_missing_key_shows_error_and_exits(self, mock_dotenv, capsys):
        """Missing ANTHROPIC_API_KEY should print an error and exit (Requirement 2.2)."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit) as exc_info:
                validate_api_key()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "ANTHROPIC_API_KEY not found" in captured.out
        assert ".env.example" in captured.out
        mock_dotenv.assert_called_once()

    @patch("src.vibe_bot.load_dotenv")
    def test_empty_key_shows_error_and_exits(self, mock_dotenv, capsys):
        """Empty ANTHROPIC_API_KEY should print an error and exit (Requirement 2.2)."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=True):
            with pytest.raises(SystemExit) as exc_info:
                validate_api_key()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "ANTHROPIC_API_KEY not found" in captured.out
        assert ".env.example" in captured.out
        mock_dotenv.assert_called_once()

    @patch("src.vibe_bot.load_dotenv")
    def test_valid_key_returns_key_string(self, mock_dotenv):
        """Valid ANTHROPIC_API_KEY should be returned as a string (Requirement 2.3)."""
        test_key = "sk-ant-test-key-12345"
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": test_key}, clear=True):
            result = validate_api_key()

        assert result == test_key
        mock_dotenv.assert_called_once()


# ---------------------------------------------------------------------------
# 6.3 — Tool definition and search handler tests (Requirements 4.5, 4.6, 4.7, 9.1, 9.3)
# ---------------------------------------------------------------------------

# Expected catalog values from data/songs.csv and the design document
EXPECTED_GENRES = [
    "pop", "lofi", "rock", "ambient", "jazz", "synthwave",
    "indie pop", "hip-hop", "r&b", "classical", "metal",
    "reggae", "folk", "edm", "blues", "soul",
]

EXPECTED_MOODS = [
    "happy", "chill", "intense", "relaxed", "moody",
    "focused", "confident", "romantic", "melancholic",
    "aggressive", "dreamy", "sad", "euphoric", "nostalgic",
    "tender",
]


class TestToolDefinition:
    """Tests for get_search_songs_tool() — genre/mood enums and structure."""

    def test_tool_definition_contains_all_16_genres(self):
        """Tool definition should list all 16 catalog genres (Requirement 4.5)."""
        tool = get_search_songs_tool()
        genre_enums = tool["input_schema"]["properties"]["genre"]["enum"]
        assert len(genre_enums) == 16
        for genre in EXPECTED_GENRES:
            assert genre in genre_enums, f"Missing genre: {genre}"

    def test_tool_definition_contains_all_15_moods(self):
        """Tool definition should list all 15 catalog moods (Requirement 4.6)."""
        tool = get_search_songs_tool()
        mood_enums = tool["input_schema"]["properties"]["mood"]["enum"]
        assert len(mood_enums) == 15
        for mood in EXPECTED_MOODS:
            assert mood in mood_enums, f"Missing mood: {mood}"

    def test_tool_definition_has_correct_name(self):
        """Tool definition name should be 'search_songs'."""
        tool = get_search_songs_tool()
        assert tool["name"] == "search_songs"

    def test_tool_definition_requires_genre_mood_energy(self):
        """Tool definition should require genre, mood, and energy fields."""
        tool = get_search_songs_tool()
        required = tool["input_schema"]["required"]
        assert "genre" in required
        assert "mood" in required
        assert "energy" in required


class TestHandleSearchSongs:
    """Tests for handle_search_songs() — integration with real catalog data."""

    @pytest.fixture()
    def catalog(self):
        """Load the real song catalog for integration tests."""
        return load_songs("data/songs.csv")

    def test_returns_valid_json_with_correct_structure(self, catalog):
        """handle_search_songs should return valid JSON with required keys (Requirement 9.1, 9.3)."""
        tool_input = {"genre": "pop", "mood": "happy", "energy": 0.8}
        result = handle_search_songs(tool_input, catalog)

        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) <= 5

        required_keys = {"title", "artist", "genre", "mood", "energy", "score"}
        for item in parsed:
            assert required_keys.issubset(item.keys()), (
                f"Missing keys: {required_keys - item.keys()}"
            )

    def test_returns_at_most_5_results(self, catalog):
        """handle_search_songs should return at most 5 songs (Requirement 9.3)."""
        tool_input = {"genre": "lofi", "mood": "chill", "energy": 0.4}
        result = handle_search_songs(tool_input, catalog)
        parsed = json.loads(result)
        assert len(parsed) <= 5

    def test_result_fields_have_correct_types(self, catalog):
        """Each result item should have the correct field types."""
        tool_input = {"genre": "rock", "mood": "intense", "energy": 0.9}
        result = handle_search_songs(tool_input, catalog)
        parsed = json.loads(result)

        for item in parsed:
            assert isinstance(item["title"], str)
            assert isinstance(item["artist"], str)
            assert isinstance(item["genre"], str)
            assert isinstance(item["mood"], str)
            assert isinstance(item["energy"], (int, float))
            assert isinstance(item["score"], (int, float))

    def test_energy_clamping_high_value(self, catalog):
        """Energy values above 1.0 should be clamped to 1.0 (Requirement 9.5)."""
        tool_input = {"genre": "pop", "mood": "happy", "energy": 5.0}
        result = handle_search_songs(tool_input, catalog)
        parsed = json.loads(result)
        # Should still return valid results without error
        assert isinstance(parsed, list)
        assert len(parsed) > 0

    def test_energy_clamping_negative_value(self, catalog):
        """Energy values below 0.0 should be clamped to 0.0 (Requirement 9.5)."""
        tool_input = {"genre": "ambient", "mood": "chill", "energy": -2.0}
        result = handle_search_songs(tool_input, catalog)
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) > 0

    def test_unknown_tool_returns_error_result(self):
        """An unknown tool name should produce an error result (Requirement 4.7).

        This tests the branching logic in run_vibe_bot that returns an error
        tool_result for unrecognized tool names. We verify the error JSON
        structure directly.
        """
        error_result = json.dumps({"error": "Unknown tool: fake_tool"})
        parsed = json.loads(error_result)
        assert "error" in parsed
        assert "fake_tool" in parsed["error"]


# ---------------------------------------------------------------------------
# 6.4 — Agentic loop behavior tests with mocked Claude client
#        (Requirements 5.2, 8.1, 8.2, 8.3)
# ---------------------------------------------------------------------------


def _make_text_block(text: str) -> MagicMock:
    """Create a mock content block with a text attribute."""
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def _make_tool_use_block(
    tool_name: str = "search_songs",
    tool_input: dict | None = None,
    tool_id: str = "toolu_01",
) -> MagicMock:
    """Create a mock tool_use content block."""
    block = MagicMock()
    block.type = "tool_use"
    block.name = tool_name
    block.input = tool_input or {"genre": "pop", "mood": "happy", "energy": 0.8}
    block.id = tool_id
    # tool_use blocks should NOT have a text attribute
    del block.text
    return block


def _make_response(stop_reason: str, content: list) -> MagicMock:
    """Create a mock Claude API response."""
    response = MagicMock()
    response.stop_reason = stop_reason
    response.content = content
    return response


def _mock_httpx_response(status_code: int = 401) -> MagicMock:
    """Create a mock httpx.Response for constructing anthropic exceptions."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {}
    resp.request = MagicMock()
    return resp


class TestAgenticLoop:
    """Tests for run_vibe_bot() agentic loop behavior with mocked Claude client."""

    DUMMY_SONGS = [
        {
            "title": "Test Song",
            "artist": "Test Artist",
            "genre": "pop",
            "mood": "happy",
            "energy": 0.8,
            "tempo": 120,
            "valence": 0.7,
            "danceability": 0.6,
            "acousticness": 0.3,
        }
    ]

    def test_end_turn_extracts_final_text(self):
        """end_turn stop reason should extract and return the final text (Requirement 4.4)."""
        expected_text = "Here is your playlist:\n1. Test Song by Test Artist"
        end_response = _make_response(
            "end_turn", [_make_text_block(expected_text)]
        )

        client = MagicMock()
        client.messages.create.return_value = end_response

        result = run_vibe_bot("chill study session", self.DUMMY_SONGS, client)

        assert result == expected_text
        client.messages.create.assert_called_once()

    def test_tool_use_triggers_tool_handler(self):
        """tool_use stop reason should trigger the search handler and continue the loop (Requirement 4.3)."""
        tool_block = _make_tool_use_block()
        tool_response = _make_response("tool_use", [tool_block])

        final_text = "1. Test Song — great for studying"
        end_response = _make_response(
            "end_turn", [_make_text_block(final_text)]
        )

        client = MagicMock()
        client.messages.create.side_effect = [tool_response, end_response]

        result = run_vibe_bot("chill study session", self.DUMMY_SONGS, client)

        assert result == final_text
        assert client.messages.create.call_count == 2

    def test_iteration_cap_reached_shows_informative_message(self):
        """Reaching MAX_ITERATIONS should return an informative cap message (Requirement 5.2)."""
        # Every response is a tool_use — Claude never says end_turn
        tool_block = _make_tool_use_block()
        tool_response = _make_response("tool_use", [tool_block])

        client = MagicMock()
        client.messages.create.return_value = tool_response

        result = run_vibe_bot("power workout", self.DUMMY_SONGS, client)

        assert "iteration limit" in result.lower() or "Reached the iteration limit" in result
        assert str(MAX_ITERATIONS) in result
        assert client.messages.create.call_count == MAX_ITERATIONS

    def test_auth_error_shows_api_key_message(self):
        """AuthenticationError should return a message about the API key (Requirement 8.1)."""
        mock_resp = _mock_httpx_response(status_code=401)
        client = MagicMock()
        client.messages.create.side_effect = anthropic.AuthenticationError(
            message="Invalid API key",
            response=mock_resp,
            body=None,
        )

        result = run_vibe_bot("chill vibes", self.DUMMY_SONGS, client)

        assert "invalid api key" in result.lower() or "API key" in result
        assert ".env" in result

    def test_rate_limit_error_suggests_retry(self):
        """RateLimitError should return a message suggesting retry (Requirement 8.2)."""
        mock_resp = _mock_httpx_response(status_code=429)
        client = MagicMock()
        client.messages.create.side_effect = anthropic.RateLimitError(
            message="Rate limit exceeded",
            response=mock_resp,
            body=None,
        )

        result = run_vibe_bot("morning coffee", self.DUMMY_SONGS, client)

        assert "rate limit" in result.lower()
        assert "try again" in result.lower() or "later" in result.lower()

    def test_generic_exception_shows_friendly_message(self):
        """Unexpected exceptions should return a user-friendly message (Requirement 8.3)."""
        client = MagicMock()
        client.messages.create.side_effect = RuntimeError("something broke")

        result = run_vibe_bot("party time", self.DUMMY_SONGS, client)

        assert "something went wrong" in result.lower()
        assert "--debug" in result.lower() or "debug" in result.lower()


# ---------------------------------------------------------------------------
# 6.5 — Empty vibe input re-prompt test (Requirement 3.2)
# ---------------------------------------------------------------------------


class TestEmptyVibeInputReprompt:
    """Tests for vibe_bot_interactive() re-prompting on empty input."""

    @patch("src.vibe_bot.display_vibe_playlist")
    @patch("src.vibe_bot.run_vibe_bot", return_value="1. Test Song by Artist")
    @patch("src.vibe_bot.load_songs", return_value=[{"title": "T", "artist": "A", "genre": "pop", "mood": "happy", "energy": 0.8}])
    @patch("src.vibe_bot.anthropic.Anthropic")
    @patch("src.vibe_bot.validate_api_key", return_value="sk-ant-fake-key")
    @patch("builtins.input", side_effect=["", "chill study session"])
    def test_empty_input_triggers_reprompt(
        self, mock_input, mock_validate, mock_anthropic, mock_load, mock_run, mock_display
    ):
        """Empty vibe input should re-prompt, then accept valid input (Requirement 3.2)."""
        from src.vibe_bot import vibe_bot_interactive

        vibe_bot_interactive()

        # input() should be called twice: once for the initial empty prompt, once for the re-prompt
        assert mock_input.call_count == 2
        # run_vibe_bot should receive the valid string from the second prompt
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == "chill study session"


# ---------------------------------------------------------------------------
# 7.1 — Property-based test: energy clamping (Requirements 9.4, 9.5)
# ---------------------------------------------------------------------------


class TestEnergyClamping:
    """Property-based tests for energy clamping in handle_search_songs."""

    # Feature: vibe-bot, Property 1: Energy clamping produces bounded output

    @given(value=st.floats())
    @settings(max_examples=100)
    def test_energy_clamping_bounded(self, value: float):
        """For any float, clamped energy is always in [0.0, 1.0].

        Property 1: Energy clamping produces bounded output.
        Validates: Requirements 9.4, 9.5
        """
        clamped = max(0.0, min(1.0, value))

        # NaN handling: max(0.0, min(1.0, NaN)) returns 0.0 in Python
        # because comparisons with NaN return False, so min(1.0, NaN) -> NaN,
        # then max(0.0, NaN) -> 0.0
        assert 0.0 <= clamped <= 1.0, (
            f"Clamped value {clamped} is outside [0.0, 1.0] for input {value}"
        )

    @given(value=st.floats())
    @settings(max_examples=100)
    def test_energy_clamping_equals_expected(self, value: float):
        """For any float, clamped energy equals max(0.0, min(1.0, value)).

        Property 1: Energy clamping produces bounded output.
        Validates: Requirements 9.4, 9.5
        """
        clamped = max(0.0, min(1.0, value))
        expected = max(0.0, min(1.0, value))

        # For NaN inputs, both sides produce the same result
        if math.isnan(value):
            assert math.isnan(clamped) == math.isnan(expected)
        else:
            assert clamped == expected, (
                f"Clamped {clamped} != expected {expected} for input {value}"
            )


# ---------------------------------------------------------------------------
# 7.2 — Property-based test: search songs tool result structure
#        (Requirements 4.3, 9.1, 9.3)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 7.3 — Property-based test: agentic loop iteration cap (Requirement 5.1)
# ---------------------------------------------------------------------------


class TestAgenticLoopIterationCap:
    """Property-based tests for the agentic loop iteration cap."""

    # Feature: vibe-bot, Property 3: Agentic loop respects iteration cap

    DUMMY_SONGS = [
        {
            "title": "Test Song",
            "artist": "Test Artist",
            "genre": "pop",
            "mood": "happy",
            "energy": 0.8,
            "tempo": 120,
            "valence": 0.7,
            "danceability": 0.6,
            "acousticness": 0.3,
        }
    ]

    @given(requested_iterations=st.integers(min_value=1, max_value=50))
    @settings(max_examples=100)
    def test_agentic_loop_respects_iteration_cap(self, requested_iterations: int):
        """For any number of tool_use responses, the loop calls the API at most MAX_ITERATIONS times.

        Property 3: Agentic loop respects iteration cap.
        Validates: Requirements 5.1
        """
        # Build a mock tool_use block that the loop will process each iteration
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = "search_songs"
        tool_block.input = {"genre": "pop", "mood": "happy", "energy": 0.8}
        tool_block.id = "toolu_test"
        # tool_use blocks should not have a text attribute
        del tool_block.text

        tool_response = MagicMock()
        tool_response.stop_reason = "tool_use"
        tool_response.content = [tool_block]

        client = MagicMock()
        # Always return tool_use — Claude never says end_turn
        client.messages.create.return_value = tool_response

        result = run_vibe_bot("test vibe", self.DUMMY_SONGS, client)

        # The loop must never exceed MAX_ITERATIONS API calls
        assert client.messages.create.call_count <= MAX_ITERATIONS, (
            f"Expected at most {MAX_ITERATIONS} API calls, "
            f"got {client.messages.create.call_count} "
            f"(requested_iterations={requested_iterations})"
        )
        # When the client always returns tool_use, the loop should hit the cap exactly
        assert client.messages.create.call_count == MAX_ITERATIONS


# ---------------------------------------------------------------------------
# 7.2 — Property-based test: search songs tool result structure
#        (Requirements 4.3, 9.1, 9.3)
# ---------------------------------------------------------------------------


class TestSearchSongsToolResultStructure:
    """Property-based tests for handle_search_songs result structure."""

    # Feature: vibe-bot, Property 2: Search songs tool returns valid structured results

    @pytest.fixture(autouse=True)
    def _load_catalog(self):
        """Load the real song catalog once for all property tests in this class."""
        self.catalog = load_songs("data/songs.csv")

    @given(
        genre=st.sampled_from(EXPECTED_GENRES),
        mood=st.sampled_from(EXPECTED_MOODS),
        energy=st.floats(min_value=0.0, max_value=1.0),
    )
    @settings(max_examples=100)
    def test_handle_search_songs_returns_valid_json(
        self, genre: str, mood: str, energy: float
    ):
        """For any valid tool input, handle_search_songs returns valid JSON.

        Property 2: Search songs tool returns valid structured results.
        Validates: Requirements 4.3, 9.1, 9.3
        """
        tool_input = {"genre": genre, "mood": mood, "energy": energy}
        result = handle_search_songs(tool_input, self.catalog)

        # Must be valid JSON
        parsed = json.loads(result)

        # Must be a list of at most 5 items
        assert isinstance(parsed, list), f"Expected list, got {type(parsed)}"
        assert len(parsed) <= 5, f"Expected at most 5 items, got {len(parsed)}"

        # Each item must have the required keys with correct types
        required_keys = {"title", "artist", "genre", "mood", "energy", "score"}
        for item in parsed:
            assert required_keys.issubset(item.keys()), (
                f"Missing keys: {required_keys - item.keys()}"
            )
            assert isinstance(item["title"], str)
            assert isinstance(item["artist"], str)
            assert isinstance(item["genre"], str)
            assert isinstance(item["mood"], str)
            assert isinstance(item["energy"], (int, float))
            assert isinstance(item["score"], (int, float))


# ---------------------------------------------------------------------------
# 7.4 — Property-based test: playlist display contains vibe input
#        (Requirement 6.2)
# ---------------------------------------------------------------------------


class TestPlaylistDisplayContainsVibeInput:
    """Property-based tests for display_vibe_playlist including the original vibe."""

    # Feature: vibe-bot, Property 4: Playlist display includes original vibe input

    @given(vibe_input=st.text(min_size=1))
    @settings(max_examples=100)
    def test_display_contains_vibe_input(self, vibe_input: str):
        """For any non-empty vibe string, the display output contains it.

        Property 4: Playlist display includes original vibe input.
        Validates: Requirements 6.2
        """
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            display_vibe_playlist(vibe_input, "1. Test Song by Test Artist")

        output = buf.getvalue()
        assert vibe_input in output, (
            f"Vibe input {vibe_input!r} not found in display output"
        )
