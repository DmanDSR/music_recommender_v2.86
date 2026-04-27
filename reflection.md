# Reflection — AI Ethics, Reliability, and Collaboration

---

## What are the limitations or biases in your system?

Energy runs the show. After bumping the weight to ×3.0, a perfect energy match alone (3.0 points) beats a perfect genre + mood match combined (2.75). So a metal song can land in a jazz listener's top 5 just because the energy is close — and the system has no idea that's wrong. On top of that, mood is all-or-nothing ("chill" and "relaxed" score zero against each other), and 14 of 16 genres only have one song, so once that genre bonus fires the rest of the list is just whatever's closest on energy.

---

## Could your AI be misused, and how would you prevent that?

Honestly, the risk is low — it recommends songs from a fixed 19-song catalog, so the worst case is a bad playlist. The main guardrail is the 6-call iteration cap, which prevents someone from crafting inputs that make Claude loop forever and burn API credits. If this were scaled to a real catalog, the energy-dominant weights would need a serious rework — users would trust recommendations without realizing the system ran out of relevant songs three picks in.

---

## What surprised you while testing your AI's reliability?

Property-based testing caught things I never would have thought to check. Hypothesis sent `NaN` as an energy value and it sailed right through the clamping function — no unit test would think to try that. The other surprise was how good bad output looks. Two profiles with nearly identical energy but completely different genre/mood preferences got 4 of 5 songs in common, and you'd never notice without checking the score breakdowns.

---

## AI Collaboration

I used Claude (via Kiro) for code generation, debugging, tests, and docs throughout the project.

**Helpful:** AI suggested stress-testing the iteration cap by mocking Claude to always return `tool_use` and verifying the loop still stops at 6. My original plan was just checking the constant existed — the AI's version actually proves the guardrail works under adversarial conditions.

**Flawed:** Early on, AI wanted to keep `pandas` and `streamlit` in `requirements.txt` "for future use" even though neither was imported anywhere. Dead dependencies confuse anyone setting up the project. I caught it and removed both.
