import csv
import os

def implied_probability(odds):
    """Converts American odds to implied probability."""
    try:
        odds = float(odds)
        if odds > 0:
            return 100.0 / (odds + 100.0)
        elif odds < 0:
            return abs(odds) / (abs(odds) + 100.0)
        return 0.5
    except (ValueError, TypeError):
        return 0.5

def convert_data(input_file, output_file):
    print(f"🚀 Starting conversion: {input_file} -> {output_file}")
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"❌ ERROR: Could not find {input_file}")
        return

    converted_rows = []
    
    with open(input_file, mode='r', encoding='utf-8', errors='ignore') as infile:
        reader = csv.DictReader(infile)
        
        # Check headers to adapt to different CSV structures
        headers = reader.fieldnames
        if not headers:
            print("❌ ERROR: Empty CSV.")
            return
            
        # Helper to find the right column name regardless of case/spacing
        def get_col_name(possible_names):
            for name in possible_names:
                for header in headers:
                    if name.lower() in header.lower():
                        return header
            return None

        home_team_col = get_col_name(["home", "team1", "favorite"])
        away_team_col = get_col_name(["away", "team2", "underdog"])
        home_odds_col = get_col_name(["home_odds", "home_moneyline", "home_line"])
        away_odds_col = get_col_name(["away_odds", "away_moneyline", "away_line"])

        if not all([home_team_col, away_team_col, home_odds_col, away_odds_col]):
            print("❌ ERROR: Could not find the required columns in the CSV.")
            print(f"Found headers: {headers}")
            print("Please check the column names.")
            return

        for row in reader:
            team_a = row[home_team_col]
            odds_a = row[home_odds_col]
            team_b = row[away_team_col]
            odds_b = row[away_odds_col]
            
            # Skip empty rows
            if not team_a or not team_b or not odds_a or not odds_b:
                continue

            # Calculate the "Vig Stripped" probability
            raw_prob_a = implied_probability(odds_a)
            raw_prob_b = implied_probability(odds_b)
            total_implied = raw_prob_a + raw_prob_b
            
            if total_implied <= 0:
                continue
                
            # Normalize so they equal 100%
            true_prob_a = raw_prob_a / total_implied
            
            converted_rows.append({
                "team_a": team_a,
                "team_a_odds": odds_a,
                "team_b": team_b,
                "team_b_odds": odds_b,
                "model_prob_a": round(true_prob_a, 4)
            })

    # Write the converted data
    with open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
        fieldnames = ["team_a", "team_a_odds", "team_b", "team_b_odds", "model_prob_a"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(converted_rows)
        
    print(f"✅ Success! Converted {len(converted_rows)} games.")
    print(f"📁 Saved to: {output_file}")

if __name__ == "__main__":
    # --- CONFIGURATION ---
    # Change this to the name of the file you downloaded from Zenodo
    INPUT_CSV = "NFL_Data.csv" 
    # This is the file you will upload to Ben's app
    OUTPUT_CSV = "nfl_template_historical.csv"
    
    convert_data(INPUT_CSV, OUTPUT_CSV)
