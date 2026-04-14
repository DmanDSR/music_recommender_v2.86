"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

try:
    from recommender import load_songs, recommend_songs       # python src/main.py
except ModuleNotFoundError:
    from src.recommender import load_songs, recommend_songs   # python -m src.main

WIDTH = 62
MAX_SCORE = 5.75  # genre(1.25) + mood(1.5) + energy(3.0)


def score_bar(score: float, width: int = 20) -> str:
    filled = round((score / MAX_SCORE) * width)
    return "#" * filled + "-" * (width - filled)


def display_recommendations(recommendations) -> None:
    print("\n" + "=" * WIDTH)
    print(f"  Top {len(recommendations)} Music Recommendations")
    print("=" * WIDTH)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        reasons = explanation.split("; ")
        bar = score_bar(score)

        print(f"\n  #{rank}  {song['title']}  -  {song['artist']}")
        print(f"       Score: {score:.2f} / {MAX_SCORE:.1f}   [{bar}]")
        print(f"       {'-' * (WIDTH - 8)}")
        for reason in reasons:
            print(f"       * {reason}")

    print("\n" + "=" * WIDTH + "\n")


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded {len(songs)} songs from catalog.")

    user_profiles = [
        {
            "name": "High-Energy Pop",
            "genre": "pop",
            "mood": "happy",
            "energy": 0.9,
        },
        {
            "name": "Chill Lofi",
            "genre": "lofi",
            "mood": "chill",
            "energy": 0.35,
        },
        {
            "name": "Deep Intense Rock",
            "genre": "rock",
            "mood": "intense",
            "energy": 0.92,
        },
    ]

    for profile in user_profiles:
        name = profile["name"]
        user_prefs = {k: v for k, v in profile.items() if k != "name"}

        print(f"\n  [{name}] -> genre: {user_prefs['genre']} | "
              f"mood: {user_prefs['mood']} | energy: {user_prefs['energy']}")

        recommendations = recommend_songs(user_prefs, songs, k=5)
        display_recommendations(recommendations)


if __name__ == "__main__":
    main()
