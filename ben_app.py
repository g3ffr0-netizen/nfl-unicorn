import streamlit as st
import pandas as pd
import numpy as np
import io

st.set_page_config(page_title="Ben's NFL Command Centre", layout="wide")
st.title("🏈 Ben's Sovereign NFL Command Centre [Cloud Edition]")
st.markdown("### Bulletproof Text Parser & Multi-Match Gridiron Engine.")

st.sidebar.header("Ben's Matchup Hub")
input_mode = st.sidebar.radio("Ingestion Mode", ["Paste Raw Text (Fastest)", "Manual Entry", "Multi-Game Batch CSV"])

def american_to_decimal(odds) -> float:
    try:
        odds = float(odds)
        if odds > 0: return (odds / 100.0) + 1.0
        elif odds < 0: return (100.0 / abs(odds)) + 1.0
        return 1.0
    except (ValueError, TypeError):
        return 1.0

def implied_probability(odds) -> float:
    try:
        odds = float(odds)
        if odds > 0: return 100.0 / (odds + 100.0)
        elif odds < 0: return abs(odds) / (abs(odds) + 100.0)
        return 0.5
    except (ValueError, TypeError):
        return 0.5

def process_math(team_a_odds, team_b_odds, engine_prob_a):
    try:
        float(team_a_odds)
        float(team_b_odds)
        float(engine_prob_a)
    except (ValueError, TypeError):
        return None, None, None, None

    raw_prob_a = implied_probability(team_a_odds)
    raw_prob_b = implied_probability(team_b_odds)
    total_implied = raw_prob_a + raw_prob_b
    
    if total_implied <= 0: return None, None, None, None
        
    true_prob_a = raw_prob_a / total_implied
    true_prob_b = raw_prob_b / total_implied
    dec_odds_a = american_to_decimal(team_a_odds)
    dec_odds_b = american_to_decimal(team_b_odds)
    
    engine_prob_b = 1.0 - engine_prob_a
    
    ev_a = (engine_prob_a * dec_odds_a) - 1.0
    ev_b = (engine_prob_b * dec_odds_b) - 1.0
    
    return ev_a, ev_b, true_prob_a, true_prob_b

if input_mode == "Paste Raw Text (Fastest)":
    st.markdown("### Paste Matchup Data")
    st.markdown("Copy the odds from your sportsbook and paste them below. Format: `Team A, -150, Team B, +130, 0.65` (One matchup per line).")
    
    raw_text = st.text_area("Paste here:", height=200, placeholder="Chiefs, -150, Ravens, 130, 0.58\n49ers, -180, Jets, 150, 0.66")
    
    if st.button("🚀 Process Text"):
        if raw_text.strip() == "":
            st.warning("⚠️ Please paste some text first.")
        else:
            lines = raw_text.strip().split('\n')
            results = []
            skipped = 0
            
            for line in lines:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) == 5:
                    team_a, odds_a, team_b, odds_b, prob_a = parts
                    try:
                        prob_a_float = float(prob_a)
                        ev_a, ev_b, _, _ = process_math(odds_a, odds_b, prob_a_float)
                        
                        if ev_a is None:
                            skipped += 1
                            continue
                            
                        best_play = "Pass"
                        max_ev = max(ev_a, ev_b)
                        
                        if max_ev > 0.05:
                            best_play = f"🔥 VALUE: {team_a if ev_a > ev_b else team_b}"
                        elif min(ev_a, ev_b) < -0.10:
                            best_play = f"🚩 FAKE FAV: {team_a if ev_a < ev_b else team_b}"

                        results.append({
                            "Matchup": f"{team_a} vs {team_b}",
                            "Team A EV": f"{ev_a*100:+.1f}%",
                            "Team B EV": f"{ev_b*100:+.1f}%",
                            "Action": best_play
                        })
                    except ValueError:
                        skipped += 1
                else:
                    skipped += 1
                    
            if skipped > 0:
                st.warning(f"🛡️ Data Quality Shield: Skipped {skipped} lines that didn't match the 5-column format.")
                
            if results:
                st.success(f"✅ Processed {len(results)} matchups successfully.")
                st.dataframe(pd.DataFrame(results), use_container_width=True)
            else:
                st.error("🚨 No valid matchups found. Check your formatting.")

elif input_mode == "Manual Entry":
    team_a_name = st.sidebar.text_input("Team A Name", "San Francisco 49ers")
    team_a_odds = st.sidebar.number_input("Team A Odds (American)", value=-140, step=5)
    team_b_name = st.sidebar.text_input("Team B Name", "Dallas Cowboys")
    team_b_odds = st.sidebar.number_input("Team B Odds (American)", value=120, step=5)
    engine_prob_a = st.sidebar.slider(f"{team_a_name} True Probability (%)", 1.0, 99.0, 60.0, 0.5) / 100.0
    
    ev_a, ev_b, true_prob_a, true_prob_b = process_math(team_a_odds, team_b_odds, engine_prob_a)
    
    if ev_a is not None:
        col1, col2, col3 = st.columns(3)
        total_vig = (implied_probability(team_a_odds) + implied_probability(team_b_odds) - 1.0) * 100
        col1.metric("Bookie Overround (Vig)", f"{total_vig:.2f}%")
        col2.metric(f"{team_a_name} Market Prob", f"{true_prob_a*100:.1f}%")
        col3.metric(f"{team_b_name} Market Prob", f"{true_prob_b*100:.1f}%")

        st.markdown("---")
        st.subheader("📊 Value Matrix & Expected Value (EV)")
        res_col1, res_col2 = st.columns(2)

        with res_col1:
            st.markdown(f"### {team_a_name}")
            st.write(f"**Decimal Odds:** ${american_to_decimal(team_a_odds):.2f}")
            st.write(f"**Model Probability:** {engine_prob_a*100:.1f}%")
            st.write(f"**Expected Value (EV):** `{ev_a*100:+.2f}%`")
            if ev_a > 0.05: st.success("🏈 TOUCHDOWN VALUE!")
            elif ev_a < -0.10: st.error("🚩 FAKE FAVOURITE")
            else: st.info("Pass")

        with res_col2:
            st.markdown(f"### {team_b_name}")
            st.write(f"**Decimal Odds:** ${american_to_decimal(team_b_odds):.2f}")
            st.write(f"**Model Probability:** {(1-engine_prob_a)*100:.1f}%")
            st.write(f"**Expected Value (EV):** `{ev_b*100:+.2f}%`")
            if ev_b > 0.05: st.success("🏈 TOUCHDOWN VALUE!")
            elif ev_b < -0.10: st.error("🚩 FAKE FAVOURITE")
            else: st.info("Pass")

else:
    st.markdown("### Multi-Game Batch Ingestion")
    
    sample_csv = "team_a,team_a_odds,team_b,team_b_odds,model_prob_a\nChiefs,-130,Ravens,110,0.58\n49ers,-180,Jets,150,0.66"
    st.download_button(label="📥 Download Sample CSV Template", data=sample_csv, file_name="nfl_template.csv", mime="text/csv")
    
    st.markdown("Upload a CSV with exact columns: `team_a`, `team_a_odds`, `team_b`, `team_b_odds`, `model_prob_a`")
    uploaded_file = st.sidebar.file_uploader("Upload Batch CSV", type=["csv"])
    
    if uploaded_file is not None:
        st.session_state['uploaded_df'] = uploaded_file.getvalue()
        
    if 'uploaded_df' in st.session_state and st.session_state['uploaded_df'] is not None:
        try:
            content = st.session_state['uploaded_df']
            if len(content) == 0:
                st.sidebar.error("⚠️ Uploaded CSV file is completely empty (0 bytes).")
            else:
                df = pd.read_csv(io.BytesIO(content), on_bad_lines="skip")
                if df.empty:
                    st.warning("⚠️ Uploaded CSV has no rows to parse.")
                else:
                    required_cols = ['team_a', 'team_a_odds', 'team_b', 'team_b_odds', 'model_prob_a']
                    if not all(col in df.columns for col in required_cols):
                        st.error(f"🚨 Missing required columns. Required: {required_cols}")
                    else:
                        results = []
                        skipped = 0
                        for index, row in df.iterrows():
                            ev_a, ev_b, _, _ = process_math(row['team_a_odds'], row['team_b_odds'], row['model_prob_a'])
                            if ev_a is None:
                                skipped += 1
                                continue
                                
                            best_play = "Pass"
                            max_ev = max(ev_a, ev_b)
                            
                            if max_ev > 0.05:
                                best_play = f"🔥 VALUE: {row['team_a'] if ev_a > ev_b else row['team_b']}"
                            elif min(ev_a, ev_b) < -0.10:
                                best_play = f"🚩 FAKE FAV: {row['team_a'] if ev_a < ev_b else row['team_b']}"

                            results.append({
                                "Matchup": f"{row['team_a']} vs {row['team_b']}",
                                "Team A EV": f"{ev_a*100:+.1f}%",
                                "Team B EV": f"{ev_b*100:+.1f}%",
                                "Action": best_play
                            })
                        
                        if skipped > 0:
                            st.warning(f"🛡️ Data Quality Shield: Skipped {skipped} invalid rows.")
                        if results:
                            st.success(f"✅ Processed {len(results)} matchups successfully.")
                            st.dataframe(pd.DataFrame(results), use_container_width=True)
                        else:
                            st.error("🚨 No valid matchups could be processed.")
        except Exception as e:
            st.error(f"⚠️ Error parsing CSV batch: {e}")
    else:
        st.info("👈 Upload a CSV file via the sidebar to process multiple games concurrently.")