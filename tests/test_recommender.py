from src.recommender import Song, UserProfile, Recommender, score_song, recommend_songs


# --- Test data ---

def _pop_song() -> Song:
    return Song(
        id=1,
        title="Test Pop Track",
        artist="Test Artist",
        genre="pop",
        mood="happy",
        energy=0.8,
        tempo_bpm=120,
        valence=0.9,
        danceability=0.8,
        acousticness=0.2,
    )


def _lofi_song() -> Song:
    return Song(
        id=2,
        title="Chill Lofi Loop",
        artist="Test Artist",
        genre="lofi",
        mood="chill",
        energy=0.4,
        tempo_bpm=80,
        valence=0.6,
        danceability=0.5,
        acousticness=0.9,
    )


def make_small_recommender() -> Recommender:
    return Recommender([_pop_song(), _lofi_song()])


# --- Recommender class tests ---

def test_recommend_returns_correct_count():
    rec = make_small_recommender()
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    results = rec.recommend(user, k=2)
    assert len(results) == 2


def test_recommend_ranks_matching_song_first():
    """A pop/happy user should get the pop song ranked above the lofi song."""
    rec = make_small_recommender()
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    results = rec.recommend(user, k=2)
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"
    assert results[1].genre == "lofi"


def test_recommend_ranks_lofi_first_for_lofi_user():
    """A lofi/chill user should get the lofi song ranked above the pop song."""
    rec = make_small_recommender()
    user = UserProfile(
        favorite_genre="lofi",
        favorite_mood="chill",
        target_energy=0.4,
        likes_acoustic=True,
    )
    results = rec.recommend(user, k=2)
    assert results[0].genre == "lofi"
    assert results[0].mood == "chill"


def test_recommend_respects_k_limit():
    rec = make_small_recommender()
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    results = rec.recommend(user, k=1)
    assert len(results) == 1


def test_explain_recommendation_contains_score_and_reasons():
    rec = make_small_recommender()
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    explanation = rec.explain_recommendation(user, _pop_song())
    assert isinstance(explanation, str)
    assert "Score:" in explanation
    assert "genre match" in explanation
    assert "mood match" in explanation
    assert "energy proximity" in explanation


def test_explain_recommendation_shows_misses():
    rec = make_small_recommender()
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    explanation = rec.explain_recommendation(user, _lofi_song())
    assert "genre miss" in explanation
    assert "mood miss" in explanation


# --- Standalone function tests ---

def test_score_song_perfect_match():
    """A song that matches genre, mood, and energy exactly should score 5.75."""
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    song = {"genre": "pop", "mood": "happy", "energy": 0.8}
    score, reasons = score_song(user_prefs, song)
    assert score == 1.25 + 1.5 + 3.0  # 5.75
    assert any("genre match" in r for r in reasons)
    assert any("mood match" in r for r in reasons)


def test_score_song_no_match():
    """A song with wrong genre, wrong mood, and opposite energy scores low."""
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.9}
    song = {"genre": "classical", "mood": "melancholic", "energy": 0.1}
    score, reasons = score_song(user_prefs, song)
    # No genre or mood bonus, energy contribution = (1.0 - 0.8) * 3.0 = 0.6
    assert score < 1.0
    assert any("genre miss" in r for r in reasons)
    assert any("mood miss" in r for r in reasons)


def test_recommend_songs_returns_sorted_results():
    """recommend_songs should return results sorted by score, highest first."""
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    songs = [
        {"genre": "lofi", "mood": "chill", "energy": 0.4},
        {"genre": "pop", "mood": "happy", "energy": 0.8},
    ]
    results = recommend_songs(user_prefs, songs, k=2)
    assert results[0][1] > results[1][1]  # first score > second score
    assert results[0][0]["genre"] == "pop"
