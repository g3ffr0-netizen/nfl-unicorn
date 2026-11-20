# 🏈 Nebo Blokes NFL Command Centre [The Unicorn Engine]

Welcome to the **Nebo Blokes NFL Command Centre**!  
Built on 60+ years of historical NFL data (14,239+ games from 1966–Latest), this engine strips away the bookmaker's margin (the **Vig**), applies **PLE (Posterior Likelihood Estimation) Shrinkage** to prevent overconfidence on small samples, and sizes bets automatically using **Fractional Kelly Criterion**.

---

## 🧭 Command Centre Modes (Buttons 1–4)

Use the **Command Centre Mode** radio buttons in the left sidebar to switch between workflows:

### 1. Week Ahead Slate Scanner (Spread + O/U + PLE)
Your weekly bulk-scanning radar for finding value across the entire NFL round at once.
* **How to use it:** Set **Home Team Order** (`Team 1 is Away` if pasting standard US *"Dolphins at Bills"* schedules, or `Team 1 is Home` if pasting Aussie *"Bills vs Dolphins"* schedules), paste your comma-separated slate (`Team 1, Team 2, Spread, O/U`), and run the scan.
* **What it shows:** Compares the bookmaker's spread and Over/Under total against the model's fair line, flagging **🔥 VALUE BET** opportunities that clear your **Minimum EV Gate (%)** along with recommended dollar stakes.

### 2. Full Matchup Lab (Weather, Rest, ML, Spread, O/U)
A deep-dive simulator for single games where situational factors matter.
* **How to use it:** Select the **Home Team** and **Away Team**, enter American Moneyline odds (e.g. `-180` for favourites, `+155` for underdogs) and the Sportsbook Over/Under line, then dial in **Rest Status** (Normal, Short Week, Bye Week), **Forecast Wind (mph)**, **Forecast Temp (°F)**, **Neutral Site** (for International games), and **Rain / Snow**.
* **What it shows:** Recalculates win probability, fair spread, and total points in real time to flag Moneyline, Spread, or Totals edges—or tells you to **PASS** when the vig eats the edge.

### 3. Feed & Lock New Results / Weekly Data
Keeps the engine's Elo ratings and team stats up to date after each week's games finish.
* **How to use it:** Enter completed game scores manually or upload a weekly CSV file, then click **🔒 Lock Scores & Recalculate Engine**.
* **How it saves:** If `GITHUB_TOKEN` is configured in Streamlit Secrets, new results commit automatically to `nfl_live_updates.csv` in your GitHub repo so they survive app reboots. Otherwise, click the **Download Updated Backup** button right underneath to save a local copy.

### 4. Power Rankings, ATS & Historical Log
Your bird's-eye view of the entire league and historical database.
* **What it shows:** Current live **Elo Power Rankings** for all 32 NFL franchises, rolling offensive/defensive efficiency metrics, Against-The-Spread (ATS) trends, and a searchable log of past games locked into the database.

---

## 📥📤 How to Upload & Download Data

### Uploading Weekly Odds (Mode 1)
Format each game on its own line as:
```text
Away Team, Home Team, Home Spread, Over/Under
Dolphins, Bills, -16.5, 44.5
Steelers, Eagles, 4.5, 38.5
