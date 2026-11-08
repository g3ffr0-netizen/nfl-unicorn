# 🏈 Ben's Sovereign NFL Command Centre [The Unicorn Engine]

Welcome to the Unicorn Engine, Ben!

This is a custom-built, cloud-hosted analytics dashboard designed to strip away the bookmaker's margin (the "Vig") and find true mathematical value in NFL matchups.

## 🚀 How to Use the Engine
When you open the app, look at the left sidebar. You have three ways to feed data into the engine:

1. **Paste Raw Text (Fastest):** Copy the odds from your sportsbook and paste them in the format `Team A, -150, Team B, +130, 0.65` (Probability must be a decimal).
2. **Manual Entry:** Use the sliders and input boxes to calculate a single matchup in real-time.
3. **Multi-Game Batch CSV:** Upload a spreadsheet of the whole week's games to find value across the board.

## 🧠 How the Math Works
The engine doesn't guess. It does two things:
* **Strips the Vig:** It takes the bookie's odds, converts them to implied probability, and normalizes them so they equal 100%. This gives you the true market probability.
* **Calculates EV (Expected Value):** It compares the true market probability to the Model Probability you provide. If the engine sees a massive gap, it flags a 🔥 **VALUE BET**.

## 🚩 The Fake Favourite Flag
If a team is heavily favored by the public but the math says they are overpriced, the engine flags them as a 🚩 **FAKE FAVOURITE**. Stay away from these traps!

## 🦆 The 3 Amigos
* **The Mad Scientist (Dad):** Architect and Commander.
* **Ben:** Gridiron Operator (Japan Deployment).
* **Mr. Quakers / Daffy:** The Adversarial AI that runs the math and occasionally lays an egg.

*Built with Python, Streamlit, and a healthy disrespect for the bookies.*
