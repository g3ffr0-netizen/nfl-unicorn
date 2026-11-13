import csv
import os
import math
from collections import defaultdict
from datetime import datetime

# --- PYTHAGOREAN EXPECTATION CORE ---
def calculate_pythagorean_win_prob(pts_for, pts_against, k=2.37):
    if pts_for == 0 and pts_against == 0:
        return 0.5
    try:
        numerator = math.pow(pts_for, k)
        denominator = numerator + math.pow(pts_against, k)
        return numerator / denominator
    except OverflowError:
        return 1.0 if pts_for > pts_against else 0.0

# --- SPREAD TO MONEYLINE CONVERTER ---
def spread_to_moneyline(spread, is_favorite):
    try:
        spread = abs(float(spread))
    except (ValueError, TypeError):
        return -110
        
    if spread == 0: ml = 100
    elif spread <= 1: ml = -110
    elif spread <= 3: ml = -150
    elif spread <= 6: ml = -250
    elif spread <= 7: ml = -300
    elif spread <= 10: ml = -450
    elif spread <= 14: ml = -700
    else: ml = -1000
    
    return ml if is_favorite else abs(ml) + 100

def moneyline_to_implied_prob(ml):
    try:
        ml = float(ml)
        if ml > 0: return 100.0 / (ml + 100.0)
        else: return abs(ml) / (abs(ml) + 100.0)
    except: return 0.5

# --- THE ULTIMATE CONVERTER v4.0 ---
def convert_nfl_data_ultimate(input_file, output_file, max_games=200, dampener_games=4):
    print(f"🚀 Starting ULTIMATE Conversion v4.0: {input_file} -> {output_file}")
    
    if not os.path.exists(input_file):
        print(f"❌ ERROR: Could not find {input_file}")
        return

    raw_games = []
    
    with open(input_file, mode='r', encoding='utf-8', errors='ignore') as infile:
        reader = csv.DictReader(infile)
        headers = reader.fieldnames
        
        def get_col(possible_names):
            for name in possible_names:
                for header in headers:
                    if name.lower() in header.lower():
                        return header
            return None

        date_col = get_col(["date", "schedule_date", "game_date"])
        home_col = get_col(["team_home", "home_team", "home"])
        away_col = get_col(["team_away", "away_team", "away"])
        score_home_col = get_col(["score_home", "home_score"])
        score_away_col = get_col(["score_away", "away_score"])
        spread_col = get_col(["spread_favorite", "spread"])
        fav_id_col = get_col(["team_favorite_id", "favorite_id"])

        for row in reader:
            try:
                h_team, a_team = row[home_col], row[away_col]
                h_score = float(row[score_home_col]) if row[score_home_col] else 0.0
                a_score = float(row[score_away_col]) if row[score_away_col] else 0.0
                
                if not h_team or not a_team: continue

                raw_games.append({
                    "date": row.get(date_col, "2000-01-01") if date_col else "2000-01-01",
                    "home": h_team, "away": a_team,
                    "h_score": h_score, "a_score": a_score,
                    "spread": row.get(spread_col, 0) if spread_col else 0,
                    "fav_id": row.get(fav_id_col, "") if fav_id_col else ""
                })
            except ValueError:
                continue

    # Sort Chronologically (Time-Aware)
    try:
        raw_games.sort(key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"))
    except Exception:
        print("⚠️ Warning: Date inconsistency. Using default order.")

    team_stats = defaultdict(lambda: {"pf": 0.0, "pa": 0.0, "games": 0, "wins": 0, "losses": 0})
    converted_rows = []
    value_bets_detected = 0

    for game in raw_games:
        h_team, a_team = game["home"], game["away"]
        h_stats, a_stats = team_stats[h_team], team_stats[a_team]
        
        # 1. Calculate raw Pythagorean probability
        h_pyth_prob = calculate_pythagorean_win_prob(h_stats["pf"], h_stats["pa"])
        a_pyth_prob = calculate_pythagorean_win_prob(a_stats["pf"], a_stats["pa"])
        
        # 2. Apply the Dampener (Early season = 50/50 prior)
        h_weight = min(1.0, h_stats["games"] / dampener_games)
        a_weight = min(1.0, a_stats["games"] / dampener_games)
        
        h_adjusted_prob = (h_pyth_prob * h_weight) + (0.5 * (1 - h_weight))
        a_adjusted_prob = (a_pyth_prob * a_weight) + (0.5 * (1 - a_weight))
        
        # 3. ULTIMATE RESULT: Opponent Quality Adjustment
        # If a team has beaten good teams, boost their prob. If they beat bad teams, reduce it.
        # (Simplified ELO-style adjustment)
        h_quality_boost = (h_stats["wins"] - h_stats["losses"]) * 0.01 
        a_quality_boost = (a_stats["wins"] - a_stats["losses"]) * 0.01
        
        h_final_prob = max(0.05, min(0.95, h_adjusted_prob + h_quality_boost))
        a_final_prob = max(0.05, min(0.95, a_adjusted_prob + a_quality_boost))
        
        total_prob = h_final_prob + a_final_prob
        model_prob_a = (h_final_prob / total_prob) if total_prob > 0 else 0.5

        # 4. Convert Spread to Moneyline
        is_home_fav = h_team in game["fav_id"] or a_team not in game["fav_id"]
        h_moneyline = spread_to_moneyline(game["spread"], is_home_fav)
        a_moneyline = spread_to_moneyline(game["spread"], not is_home_fav)

        # 5. Value Bet Diagnostics
        implied_prob_a = moneyline_to_implied_prob(h_moneyline)
        if model_prob_a > implied_prob_a + 0.05:
            value_bets_detected += 1

        converted_rows.append({
            "team_a": h_team,
            "team_a_odds": h_moneyline,
            "team_b": a_team,
            "team_b_odds": a_moneyline,
            "model_prob_a": round(model_prob_a, 4)
        })

        # Update stats AFTER prediction
        team_stats[h_team]["pf"] += game["h_score"]
        team_stats[h_team]["pa"] += game["a_score"]
        team_stats[h_team]["games"] += 1
        team_stats[a_team]["pf"] += game["a_score"]
        team_stats[a_team]["pa"] += game["h_score"]
        team_stats[a_team]["games"] += 1
        
        if game["h_score"] > game["a_score"]:
            team_stats[h_team]["wins"] += 1
            team_stats[a_team]["losses"] += 1
        else:
            team_stats[h_team]["losses"] += 1
            team_stats[a_team]["wins"] += 1

    final_output = converted_rows[-max_games:] if len(converted_rows) > max_games else converted_rows

    with open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
        fieldnames = ["team_a", "team_a_odds", "team_b", "team_b_odds", "model_prob_a"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(final_output)
        
    print(f"✅ Success! Processed {len(converted_rows)} total games.")
    print(f"✂️ Trimmed to the most recent {len(final_output)} matchups.")
    print(f"🔍 Diagnostic Edge: Detected {value_bets_detected} historical value-bet opportunities (>5% edge).")
    print(f"📁 Saved to: {output_file}")

if __name__ == "__main__":
    INPUT_CSV = "spreadspoke_scores.csv" 
    OUTPUT_CSV = "nfl_template_historical.csv"
    convert_nfl_data_ultimate(INPUT_CSV, OUTPUT_CSV, max_games=200)
