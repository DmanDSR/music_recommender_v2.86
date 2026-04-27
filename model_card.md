# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeMatch 1.0**

---

## 2. Intended Use  

VibeMatch takes a genre, mood, and energy preference and returns the 5 closest songs from a 19-song catalog. You tell it what you like — no history, no account needed. It is a classroom simulation, not a real product. It should not be used on a larger catalog without reworking the weights.

---

## 3. How the Model Works  

Every song gets scored against the user's preferences. Genre and mood are binary — match earns points, miss earns zero. Energy is different — songs earn partial credit based on how close they are to the user's target, so a near match still counts. The scores are totaled, sorted highest to lowest, and the top five are returned with a plain-language explanation for each pick. The one change from the starter was doubling energy's weight (×1.5 → ×3.0) and cutting genre's bonus in half (2.5 → 1.25), which makes energy the dominant signal.

---

## 4. Data  

19 songs loaded from a CSV. Each song has a genre, mood, energy (0–1), tempo, valence, danceability, and acousticness. The catalog covers 16 genres, but 14 of them have exactly one song — so the genre bonus fires once and energy takes over from there. The energy distribution is also uneven: most songs cluster low (0.30–0.50) or high (0.75–0.96), with only one song in the middle. No lyrics, no listener history, no collaborative signals — audio features only.

---

## 5. Strengths  

The system works well when the user's preferences are clear and the catalog has songs to match. Profiles with very different energy levels — like the Studier (0.38) and the Workout User (0.90) — return clean, non-overlapping lists. Every recommendation is fully explainable — you can see the exact score breakdown for each song, which is the biggest advantage over a black-box model.

---

## 6. Limitations and Bias 

Energy scoring can now mathematically outrank a combined genre and mood match. After doubling the multiplier to ×3.0, a song with perfect energy but no genre or mood overlap scores 3.0 — which beats a perfect genre plus mood match with no energy overlap at 2.75. Only one song sits in the 0.5–0.7 energy range, so medium-energy users get pushed toward the extremes. With 14 of 16 genres at one song each, niche preferences like classical or folk get one genre bonus and then the rest of the list defaults to energy.

---

## 7. Evaluation  

I tested three profiles: the Late Night Studier (lofi, focused, 0.38), the Workout User (pop, intense, 0.90), and the Sunday Morning Listener (jazz, relaxed, 0.40). The Studier and Workout returned zero overlap — expected, since the energy gap between them is 0.52. The surprise was positions four and five in every profile: once genre and mood bonuses were spent, energy took over and surfaced genre-foreign songs — Strobe Garden (EDM) landing at rank four for a pop user, Focus Flow (lofi) landing at rank two for a jazz listener. Both are technically close on energy but contextually wrong.

---

## 8. Future Work  

Add acousticness to the scoring — it has the widest spread in the dataset (0.05–0.92) and captures a real preference that the current weights completely ignore. Expand the catalog so each genre has more than one song — right now the genre bonus is a one-time reward before the list collapses into energy. Add a no-repeat-artist rule to the ranking step — scoring and ranking are already separated in the code, so this would be a clean addition.

---

## 9. Personal Reflection  

The biggest learning moment was doubling energy's weight and watching one number change break the whole recommendation logic — a perfect energy match (3.0 points) now beats a perfect genre plus mood match (2.75), and I did not see that coming until I ran the numbers. Using AI to surface the bias patterns was faster than manual testing would have been, but I still had to verify the score math by hand to actually trust what it was telling me. The part that surprised me most was how legitimate the output looks even though it is just three scoring rules — a user looking at the top five results would have no idea the system ran out of relevant songs at position four and started defaulting to whatever is closest on energy. If I kept going, the first thing I would add is acousticness to the scoring — it has the widest spread in the dataset (0.05–0.92) and would actually separate a folk fan from an EDM fan instead of letting them score the same.

On the collaboration side — AI was most helpful when it suggested stress-testing the iteration cap by mocking Claude to always request another tool call, which proved the guardrail actually works under adversarial conditions. Where it missed was wanting to keep unused dependencies like `pandas` and `streamlit` in `requirements.txt` "for future use" — dead imports just confuse people, so I removed them. For the full breakdown of AI collaboration, biases, and testing surprises, see [reflection.md](reflection.md).
