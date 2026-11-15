import csv
import os
from collections import defaultdict, deque
from datetime import datetime

# --- CONFIGURATION ---
INITIAL_ELO = 1500
K_FACTOR = 20
HOME_ADVANTAGE_ELO = 55
ROLLING_WINDOW = 16 # Changed to 16 to match the R script's logic

# Exact coefficients from the Professional R Script
SPREAD_INTERCEPT = -0.343262
SPREAD_HOME_ELO_COEF = -0.023827
SPREAD_AWAY_ELO_COEF = 0.021341

def parse_game_date(date_str):
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    return datetime(2000, 1, 1)

def calculate_elo_change(rating_a, rating_b, score_a, k=K_FACTOR):
    expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    return rating_a + k * (score_a - expected_a)

def get_rolling_avg(margin_deque):
    if not margin_deque:
        return 0.0
    return sum(margin_deque) / len(margin_deque)

def convert_data_v8(input_file, output_file, max_games=200):
    print(f"🚀 Starting ULTIMATE Conversion v8.0: {input_file} -> {output_file}")
    
    if not os.path.exists(input_file):
        print(f"❌ ERROR: Could not find '{input_file}'.")
        return

    raw_games = []
    
    # The Shroomozzle Shield: Force UTF-8-sig reading and strip spaces
    try:
        with open(input_file, mode='r', encoding='utf-8-sig', errors='ignore') as infile:
            reader = csv.DictReader(infile)
            
            if not reader.fieldnames:
                print("❌ ERROR: The CSV file is empty or has no headers.")
                return
                
            reader.fieldnames = [h.strip() for h in reader.fieldnames]
            headers = reader.fieldnames
            
            def get_col(possible_names):
                for name in possible_names:
                    for header in headers:
                        if header and name.lower() in header.lower():
                            return header
                return None

            date_col = get_col(["schedule_date", "date"])
            home_col = get_col(["team_home", "home"])
            away_col = get_col(["team_away", "away"])
            score_home_col = get_col(["score_home"])
            score_away_col = get_col(["score_away"])
            spread_col = get_col(["spread_favorite"])
            fav_id_col = get_col(["team_favorite_id"])
            wind_col = get_col(["weather_wind_mph"]) # Added weather

            if not all([home_col, away_col, score_home_col, score_away_col]):
                print(f"❌ ERROR: Missing critical columns.")
                return

            for row in reader:
                try:
                    if not row.get(spread_col) or not row.get(fav_id_col):
                        continue
                        
                    # Parse wind speed for weather factor
                    wind_speed = 0.0
                    if wind_col and row.get(wind_col):
                        try:
                            wind_speed = float(row[wind_col])
                        except ValueError:
                            pass
                        
                    raw_games.append({
                        "date_obj": parse_game_date(row.get(date_col, "")),
                        "home": row[home_col].strip(), 
                        "away": row[away_col].strip(),
                        "h_score": float(row[score_home_col]) if row[score_home_col] else 0.0,
                        "a_score": float(row[score_away_col]) if row[score_away_col] else 0.0,
                        "spread": float(row[spread_col]),
                        "fav_id": row[fav_id_col].strip(),
                        "wind": wind_speed
                    })
                except (ValueError, KeyError):
                    continue
    except Exception as e:
        print(f"❌ ERROR reading file: {e}")
        return

    if not raw_games:
        print("❌ ERROR: No valid games found.")
        return

    print(f"📂 Loaded {len(raw_games)} valid games with spreads.")
    raw_games.sort(key=lambda x: x["date_obj"])

    team_elos = defaultdict(lambda: INITIAL_ELO)
    team_margins = defaultdict(lambda: deque(maxlen=ROLLING_WINDOW))
    converted_rows = []
    
    # Backtest diagnostics tracker
    ats_wins = 0
    ats_losses = 0

    for game in raw_games:
        h_team = game["home"]
        a_team = game["away"]
        
        h_elo = team_elos[h_team]
        a_elo = team_elos[a_team]
        
        # Calculate the predicted spread using the exact R script formula
        predicted_spread = SPREAD_INTERCEPT + (SPREAD_HOME_ELO_COEF * h_elo) + (SPREAD_AWAY_ELO_COEF * a_elo)
        
        # Round to nearest half point
        predicted_spread = round(predicted_spread * 2) / 2
        
        # Weather Check: If wind is bad (>12mph), tighten the spread slightly
        if game["wind"] > 12:
            predicted_spread = predicted_spread * 0.9 # Reduce confidence in blowouts

        h_id = h_team.upper()
        fav_id = game["fav_id"].upper()
        is_home_fav = (fav_id in h_id) or (h_id in fav_id)
        
        bookie_spread = game["spread"] if is_home_fav else -game["spread"]
        
        # Backtest check
        actual_margin = game["h_score"] - game["a_score"]
        if (predicted_spread - bookie_spread) * (actual_margin - bookie_spread) > 0:
            ats_wins += 1
        else:
            ats_losses += 1

        converted_rows.append({
            "team_a": h_team,
            "team_a_odds": bookie_spread,
            "team_b": a_team,
            "team_b_odds": -bookie_spread,
            "model_prob_a": predicted_spread
        })

        # Update ELO and Rolling Margins AFTER the game
        if game["h_score"] > game["a_score"]: actual_result = 1.0
        elif game["h_score"] < game["a_score"]: actual_result = 0.0
        else: actual_result = 0.5
            
        new_h_elo = calculate_elo_change(h_elo + HOME_ADVANTAGE_ELO, a_elo, actual_result)
        new_a_elo = calculate_elo_change(a_elo, h_elo + HOME_ADVANTAGE_ELO, 1.0 - actual_result)
        
        team_elos[h_team] = new_h_elo - HOME_ADVANTAGE_ELO
        team_elos[a_team] = new_a_elo
        
        team_margins[h_team].append(actual_margin)
        team_margins[a_team].append(-actual_margin)

    final_output = converted_rows[-max_games:] if len(converted_rows) > max_games else converted_rows

    with open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
        fieldnames = ["team_a", "team_a_odds", "team_b", "team_b_odds", "model_prob_a"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(final_output)
        
    total_backtested = ats_wins + ats_losses
    win_pct = (ats_wins / total_backtested * 100) if total_backtested > 0 else 0.0

    print(f"\n📊 --- BACKTEST PERFORMANCE SUMMARY ---")
    print(f"Historical ATS Accuracy: {win_pct:.1f}% ({ats_wins}W - {ats_losses}L)")
    print(f"✅ Success! Processed {len(converted_rows)} total games.")
    print(f"📁 Saved to: {output_file}")

if __name__ == "__main__":
    try:
        convert_data_v8("spreadspoke_scores.csv", "nfl_template_historical.csv", max_games=200)
    except Exception as e:
        print(f"\n❌ CRITICAL CRASH: {e}")
    
    input("\nPress ENTER to exit...")
