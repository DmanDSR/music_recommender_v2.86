# Requirements Document

## Introduction

Add a Streamlit-based web interface to the VibeMatch Music Recommender, providing a browser UI for the existing Vibe Bot functionality. Users type a vibe description into a text input, click a button, and see a curated 5-song playlist rendered in the browser. This is a new entry point (`streamlit run src/app.py`) that runs alongside the existing CLI (`python -m src.main --vibe`). The web UI reuses the existing `run_vibe_bot()` pipeline — no recommendation logic is duplicated.

## Glossary

- **Web_UI**: The Streamlit-based browser interface served by `src/app.py`
- **Vibe_Input**: A free-text string describing the user's desired activity, mood, or scenario (e.g., "chill study session", "power workout")
- **Playlist_Response**: The formatted text returned by `run_vibe_bot()` containing 5 song recommendations with explanations
- **Session**: A single browser tab's interaction with the Streamlit app, managed by Streamlit's session state
- **API_Key**: The `ANTHROPIC_API_KEY` environment variable required to call the Claude API
- **Song_Catalog**: The 19-song CSV file at `data/songs.csv` loaded by `load_songs()`
- **Vibe_Bot_Pipeline**: The existing `run_vibe_bot()` function in `src/vibe_bot.py` that orchestrates the agentic loop with Claude

## Requirements

### Requirement 1: Streamlit App Entry Point

**User Story:** As a user, I want to launch the VibeMatch recommender in a web browser, so that I can interact with the Vibe Bot without using the command line.

#### Acceptance Criteria

1. WHEN the user runs `streamlit run src/app.py`, THE Web_UI SHALL start a local Streamlit server and display the VibeMatch interface in the default browser
2. THE Web_UI SHALL load the Song_Catalog from `data/songs.csv` on startup using the existing `load_songs()` function
3. THE Web_UI SHALL initialize the Anthropic client using the API_Key loaded from the `.env` file via `python-dotenv`
4. IF the API_Key is not set or is empty, THEN THE Web_UI SHALL display an error message instructing the user to configure their `.env` file

### Requirement 2: Vibe Input and Submission

**User Story:** As a user, I want to type my vibe and submit it with a button, so that I can request a playlist through the browser.

#### Acceptance Criteria

1. THE Web_UI SHALL display a text input field where the user can type a Vibe_Input
2. THE Web_UI SHALL display a submit button labeled with a descriptive action (e.g., "Get Playlist")
3. WHEN the user clicks the submit button with a non-empty Vibe_Input, THE Web_UI SHALL pass the Vibe_Input to the Vibe_Bot_Pipeline
4. IF the user clicks the submit button with an empty Vibe_Input, THEN THE Web_UI SHALL display a warning message prompting the user to enter a vibe description

### Requirement 3: Playlist Display

**User Story:** As a user, I want to see my curated playlist displayed in the browser, so that I can read the song recommendations and explanations.

#### Acceptance Criteria

1. WHEN the Vibe_Bot_Pipeline returns a Playlist_Response, THE Web_UI SHALL render the playlist text in the browser
2. WHILE the Vibe_Bot_Pipeline is processing, THE Web_UI SHALL display a spinner or loading indicator to signal that the request is in progress
3. THE Web_UI SHALL preserve the Playlist_Response on screen until the user submits a new Vibe_Input

### Requirement 4: Error Handling

**User Story:** As a user, I want to see clear error messages when something goes wrong, so that I can understand and resolve the issue.

#### Acceptance Criteria

1. IF the Vibe_Bot_Pipeline returns an error message (authentication failure, rate limit, or API error), THEN THE Web_UI SHALL display the error text to the user using a visible error indicator
2. IF the Song_Catalog file is missing or contains no valid songs, THEN THE Web_UI SHALL display an error message instead of crashing
3. IF an unexpected exception occurs during playlist generation, THEN THE Web_UI SHALL display a generic error message and log the exception details

### Requirement 5: Dependency Management

**User Story:** As a developer, I want Streamlit added to the project dependencies, so that the web UI can be installed and run by anyone following the setup instructions.

#### Acceptance Criteria

1. THE requirements.txt file SHALL include `streamlit` as a dependency
2. THE Web_UI SHALL import only from existing project modules (`src.recommender`, `src.vibe_bot`) and the `streamlit` package — no new recommendation logic SHALL be introduced

### Requirement 6: Page Layout and Branding

**User Story:** As a user, I want the web page to have a clear title and clean layout, so that the interface feels polished and easy to use.

#### Acceptance Criteria

1. THE Web_UI SHALL display a page title that identifies the application as VibeMatch
2. THE Web_UI SHALL set the browser tab title to include "VibeMatch"
3. THE Web_UI SHALL display a brief description or subtitle explaining what the tool does
