import streamlit as st
import pandas as pd
import numpy as np
import math
import os
import base64
import json
import urllib.request
from itertools import permutations
from datetime import date

st.set_page_config(
    page_title="Nilovea Racing Command Centre | PLE & Trifecta Engine",
    page_icon="🏇",
    layout="wide",
)

LIVE_RESULTS_FILE = "racing_live_results.csv"

# =====================================================================
# GITHUB PERSISTENT STORAGE HELPER (LOCKS RESULTS INTO REPO)
# =====================================================================
def push_csv_to_github(file_path: str, csv_content: str, commit_msg: str):
    """Commits updated racing results straight back into GitHub so data persists permanently."""
    token = st.secrets.get("GITHUB_TOKEN", None) if hasattr(st, "secrets") else None
    repo = st.secrets.get("GITHUB_REPO", "g3ffr0-netizen/nfl-unicorn") if hasattr(st, "secrets") else "g3ffr0-netizen/nfl-unicorn"
    if not token:
        return False, "No `GITHUB_TOKEN` found in Streamlit Secrets (saved to session & downloadable below)."

    api_url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "Nilovea-Racing-PLE-Engine",
    }

    sha = None
    try:
        req_get = urllib.request.Request(api_url, headers=headers, method="GET")
        with urllib.request.urlopen(req_get) as resp:
            existing = json.loads(resp.read().decode("utf-8"))
            sha = existing.get("sha")
    except Exception:
        sha = None

    payload = {
        "message": commit_msg,
        "content": base64.b64encode(csv_content.encode("utf-8")).decode("utf-8"),
    }
    if sha:
        payload["sha"] = sha

    try:
        req_put = urllib.request.Request(api_url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="PUT")
        with urllib.request.urlopen(req_put) as resp:
            if resp.status in (200, 201):
                return True, f"Locked permanently into `{repo}/{file_path}` on GitHub!"
            return False, f"GitHub API returned status {resp.status}"
    except Exception as e:
        return False, f"GitHub sync error: {e}"

# =====================================================================
# QUANTITATIVE RACING MATH: MULTI-RUNNER VIG, PLE, KELLY & HARVILLE
# =====================================================================
def strip_field_vig(odds_array: np.ndarray):
    """Strips bookmaker/tote overround across an N-runner field."""
    safe_odds = np.maximum(odds_array, 1.01)
    raw_imp = 1.0 / safe_odds
    overround = float(np.sum(raw_imp))
    vig_pct = (overround - 1.0) * 100.0
    p_market = raw_imp / overround
    return p_market, overround, vig_pct

def ratings_to_probs(ratings: np.ndarray, temperature: float = 12.0) -> np.ndarray:
    """Converts custom form/speed ratings (0-100 scale) into normalized win probabilities."""
    shifted = (ratings - np.max(ratings)) / max(temperature, 1.0)
    exp_r = np.exp(shifted)
    return exp_r / np.sum(exp_r)

def ple_shrinkage_field(p_market: np.ndarray, p_model: np.ndarray, shrinkage_lambda: float) -> np.ndarray:
    """Applies Posterior Likelihood Estimation (PLE) shrinkage and re-normalizes across active starters."""
    p_blend = p_market + shrinkage_lambda * (p_model - p_market)
    p_blend = np.clip(p_blend, 0.001, 0.990)
    return p_blend / np.sum(p_blend)

def kelly_fraction(p_hat: float, dec_odds: float, kelly_mult: float = 0.10) -> float:
    b = dec_odds - 1.0
    if b <= 0:
        return 0.0
    full_kelly = ((b * p_hat) - (1.0 - p_hat)) / b
    return max(0.0, full_kelly * kelly_mult)

def harville_trifecta_prob(p_vec: np.ndarray, i: int, j: int, k: int) -> float:
    """Calculates exact Harville sequential 1st (i), 2nd (j), 3rd (k) probability."""
    if len({i, j, k}) < 3:
        return 0.0
    pi, pj, pk = p_vec[i], p_vec[j], p_vec[k]
    denom_1 = max(1.0 - pi, 1e-6)
    denom_2 = max(1.0 - pi - pj, 1e-6)
    return float(pi * (pj / denom_1) * (pk / denom_2))

def harville_exacta_prob(p_vec: np.ndarray, i: int, j: int) -> float:
    if i == j:
        return 0.0
    pi, pj = p_vec[i], p_vec[j]
    return float(pi * (pj / max(1.0 - pi, 1e-6)))

# =====================================================================
# SITUATIONAL & TRACK ADJUSTMENT ENGINE (AUSTRALIAN THOROUGHBRED)
# =====================================================================
def compute_situational_rating(
    base_rating: float,
    barrier: int,
    field_size: int,
    weight_kg: float,
    track_cond: str,
    barrier_bias: str,
    wet_affinity: float,
    jt_synergy: float,
    open_odds: float,
    curr_odds: float,
    fluc_weight: float,
) -> float:
    adj = 0.0

    # 1. Barrier bias adjustment (e.g. Flemington straight outside rail vs tight turning inside rail)
    rel_barrier = (barrier - 1) / max(field_size - 1, 1)  # 0.0 = inside rail, 1.0 = wide barrier
    if barrier_bias == "Inside Rail Advantage (Tight Track)":
        adj += (0.5 - rel_barrier) * 4.0
    elif barrier_bias == "Outside / Straight Rail Advantage (e.g. Flemington)":
        adj += (rel_barrier - 0.5) * 4.0
    elif barrier_bias == "Middle Draw Ideal":
        adj += (0.25 - abs(rel_barrier - 0.5)) * 3.0

    # 2. Track condition x wet-track affinity (-5 to +5 scale)
    if track_cond in ("Soft (5-7)", "Heavy (8-10)"):
        mult = 1.0 if track_cond == "Soft (5-7)" else 1.6
        adj += wet_affinity * mult

    # 3. Weight penalty/relief relative to 56.5kg benchmark
    adj += (56.5 - weight_kg) * 0.45

    # 4. Jockey-Trainer pairing synergy (-3 to +5 rating pts)
    adj += jt_synergy

    # 5. Smart-money market fluctuation signal (steaming vs drifting)
    if open_odds > 1.0 and curr_odds > 1.0:
        imp_open = 1.0 / open_odds
        imp_curr = 1.0 / curr_odds
        fluc_delta = (imp_curr - imp_open) * 100.0  # positive = money coming in
        adj += np.clip(fluc_delta * fluc_weight, -4.0, 4.0)

    return base_rating + adj

# =====================================================================
# SIDEBAR CONTROLS (COMMAND CENTRE ARCHITECTURE)
# =====================================================================
st.sidebar.header("🏇 Nilovea Racing Command Centre")

hist_count = 0
if os.path.exists(LIVE_RESULTS_FILE):
    try:
        hist_count = len(pd.read_csv(LIVE_RESULTS_FILE))
    except Exception:
        hist_count = 0
st.sidebar.success(f"🔒 LOCKED DB: {hist_count:,} logged race results")

mode = st.sidebar.radio(
    "Command Centre Mode",
    [
        "1. Race Card Scanner (Vig Stripper + PLE + Flucs)",
        "2. Harville Trifecta & Exacta Matrix (Box / Standout)",
        "3. Track, Barrier & Jockey-Trainer Lab",
        "4. Lock Results & Model Calibration Log",
    ],
)

st.sidebar.divider()
shrinkage_lambda = st.sidebar.slider("PLE Shrinkage (λ)", 0.0, 1.0, 0.45, 0.05, help="0 = Pure Market; 1 = Pure Model Rating")
rating_temp = st.sidebar.slider("Rating Softmax Temp", 5.0, 25.0, 11.0, 0.5, help="Lower = sharper favorite separation")
min_ev = st.sidebar.slider("Minimum EV Gate (%)", 1.0, 20.0, 6.0, 0.5) / 100.0
bankroll = st.sidebar.number_input("Bankroll ($ AUD)", min_value=50.0, value=1000.0, step=50.0)
kelly_mult = st.sidebar.selectbox("Kelly Fraction", [0.10, 0.25, 0.50, 1.00], index=0, format_func=lambda x: f"{int(x*100)}% Kelly")

# =====================================================================
# DEFAULT SAMPLE RACE CARD (FLEMINGTON FEATURE)
# =====================================================================
DEFAULT_FIELD = pd.DataFrame([
    {"Active": True, "No": 1, "Horse": "Pride Of Jenni", "Barrier": 9, "Weight": 57.0, "Open Odds": 3.80, "Curr Odds": 3.40, "Form Rating": 92.5, "Wet (-5..+5)": 1.0, "J/T Synergy": 2.5},
    {"Active": True, "No": 2, "Horse": "Mr Brightside", "Barrier": 4, "Weight": 59.0, "Open Odds": 3.20, "Curr Odds": 3.50, "Form Rating": 93.0, "Wet (-5..+5)": 2.0, "J/T Synergy": 3.0},
    {"Active": True, "No": 3, "Horse": "Via Sistina", "Barrier": 7, "Weight": 57.0, "Open Odds": 4.20, "Curr Odds": 3.90, "Form Rating": 94.0, "Wet (-5..+5)": 3.0, "J/T Synergy": 3.5},
    {"Active": True, "No": 4, "Horse": "Antino", "Barrier": 11, "Weight": 59.0, "Open Odds": 8.50, "Curr Odds": 7.50, "Form Rating": 88.5, "Wet (-5..+5)": 1.5, "J/T Synergy": 2.0},
    {"Active": True, "No": 5, "Horse": "Atishu", "Barrier": 2, "Weight": 57.0, "Open Odds": 11.00, "Curr Odds": 12.00, "Form Rating": 86.0, "Wet (-5..+5)": 2.5, "J/T Synergy": 2.0},
    {"Active": True, "No": 6, "Horse": "Fangirl", "Barrier": 6, "Weight": 57.0, "Open Odds": 9.00, "Curr Odds": 10.50, "Form Rating": 87.5, "Wet (-5..+5)": 1.0, "J/T Synergy": 2.5},
    {"Active": True, "No": 7, "Horse": "Pinstriped", "Barrier": 3, "Weight": 59.0, "Open Odds": 19.00, "Curr Odds": 16.00, "Form Rating": 83.5, "Wet (-5..+5)": 2.0, "J/T Synergy": 1.0},
    {"Active": True, "No": 8, "Horse": "Buckaroo", "Barrier": 10, "Weight": 59.0, "Open Odds": 15.00, "Curr Odds": 13.00, "Form Rating": 85.0, "Wet (-5..+5)": 1.5, "J/T Synergy": 2.0},
])

if "race_field_df" not in st.session_state:
    st.session_state["race_field_df"] = DEFAULT_FIELD.copy()

# =====================================================================
# HEADER & RACE METADATA BAR
# =====================================================================
st.title("🏇 Nilovea Racing Command Centre")
st.caption("Multi-Runner Vig Stripper • PLE Shrinkage Engine • Live Scratchings & Flucs • Harville Trifecta Pricer")

c_meta1, c_meta2, c_meta3, c_meta4 = st.columns(4)
track_name = c_meta1.selectbox("Track", ["Flemington", "Randwick", "Caulfield", "Rosehill", "Moonee Valley", "Doomben", "Eagle Farm", "Other"])
race_num = c_meta2.number_input("Race #", min_value=1, max_value=12, value=8)
track_cond = c_meta3.selectbox("Track Condition", ["Good (3-4)", "Firm (1-2)", "Soft (5-7)", "Heavy (8-10)"])
barrier_bias = c_meta4.selectbox(
    "Barrier / Rail Bias",
    [
        "Neutral / Fair Track",
        "Outside / Straight Rail Advantage (e.g. Flemington)",
        "Inside Rail Advantage (Tight Track)",
        "Middle Draw Ideal",
    ],
)

def evaluate_active_field(df_in: pd.DataFrame, fluc_weight: float = 0.25):
    active_df = df_in[df_in["Active"] == True].copy().reset_index(drop=True)
    if len(active_df) < 2:
        return pd.DataFrame(), 1.0, 0.0

    # Recalculate effective barriers after scratchings
    scratched_barriers = sorted(df_in[df_in["Active"] == False]["Barrier"].tolist())
    eff_barriers = []
    for b in active_df["Barrier"]:
        shift = sum(1 for sb in scratched_barriers if sb < b)
        eff_barriers.append(max(1, int(b) - shift))
    active_df["Eff Barrier"] = eff_barriers

    field_size = len(active_df)
    p_mkt, overround, vig_pct = strip_field_vig(active_df["Curr Odds"].to_numpy(dtype=float))

    adj_ratings = []
    fluc_labels = []
    for r in active_df.itertuples(index=False):
        adj_r = compute_situational_rating(
            base_rating=float(r[7]),
            barrier=int(r[10]),
            field_size=field_size,
            weight_kg=float(r[4]),
            track_cond=track_cond,
            barrier_bias=barrier_bias,
            wet_affinity=float(r[8]),
            jt_synergy=float(r[9]),
            open_odds=float(r[5]),
            curr_odds=float(r[6]),
            fluc_weight=fluc_weight,
        )
        adj_ratings.append(adj_r)

        o_open, o_curr = float(r[5]), float(r[6])
        if o_curr < o_open * 0.90:
            fluc_labels.append(f"🔥 STEAM ({o_open:.2f}→{o_curr:.2f})")
        elif o_curr > o_open * 1.12:
            fluc_labels.append(f"❄️ DRIFT ({o_open:.2f}→{o_curr:.2f})")
        else:
            fluc_labels.append(f"➖ Steady ({o_open:.2f}→{o_curr:.2f})")

    p_mod = ratings_to_probs(np.array(adj_ratings), temperature=rating_temp)
    p_ple = ple_shrinkage_field(p_mkt, p_mod, shrinkage_lambda)

    curr_odds = active_df["Curr Odds"].to_numpy(dtype=float)
    fair_odds = 1.0 / p_ple
    ev_arr = (p_ple * curr_odds) - 1.0

    signals, stakes = [], []
    for p_val, od_val, ev_val in zip(p_ple, curr_odds, ev_arr):
        if ev_val >= min_ev:
            signals.append("🔥 VALUE WIN")
            stakes.append(bankroll * kelly_fraction(float(p_val), float(od_val), kelly_mult))
        elif ev_val > 0:
            signals.append("🟡 LEAN")
            stakes.append(0.0)
        else:
            signals.append("⚪ PASS")
            stakes.append(0.0)

    out = pd.DataFrame({
        "No": active_df["No"],
        "Horse": active_df["Horse"],
        "Eff Bar": active_df["Eff Barrier"],
        "Curr Odds": np.round(curr_odds, 2),
        "PLE Fair Odds": np.round(fair_odds, 2),
        "Market %": np.round(p_mkt * 100, 1),
        "PLE Win %": np.round(p_ple * 100, 1),
        "EV %": np.round(ev_arr * 100, 2),
        "Signal": signals,
        "Kelly Stake": [f"${s:,.2f}" for s in stakes],
        "Flucs": fluc_labels,
        "_p_ple": p_ple,
    }).sort_values("EV %", ascending=False).reset_index(drop=True)

    return out, overround, vig_pct

# =====================================================================
# MODE 1: RACE CARD SCANNER
# =====================================================================
if mode == "1. Race Card Scanner (Vig Stripper + PLE + Flucs)":
    st.subheader(f"⚡ {track_name} Race {race_num} — Live Runner & Scratching Board")

    with st.expander("📥 Upload CSV Race Card or Paste Custom Runners"):
        up_csv = st.file_uploader("Upload Race CSV (`No, Horse, Barrier, Weight, Open Odds, Curr Odds, Form Rating`)", type=["csv"])
        if up_csv is not None:
            df_loaded = pd.read_csv(up_csv)
            if "Active" not in df_loaded.columns:
                df_loaded.insert(0, "Active", True)
            for col, default_v in [("Wet (-5..+5)", 0.0), ("J/T Synergy", 0.0)]:
                if col not in df_loaded.columns:
                    df_loaded[col] = default_v
            st.session_state["race_field_df"] = df_loaded

    st.caption("Untick **Active** for live scratchings — overround, effective barriers, and PLE probabilities recalculate instantly:")
    edited_df = st.data_editor(
        st.session_state["race_field_df"],
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Active": st.column_config.CheckboxColumn("Active", default=True),
            "No": st.column_config.NumberColumn("No", format="%d"),
            "Barrier": st.column_config.NumberColumn("Bar", format="%d"),
            "Weight": st.column_config.NumberColumn("Wgt (kg)", format="%.1f"),
            "Open Odds": st.column_config.NumberColumn("Open $", format="%.2f"),
            "Curr Odds": st.column_config.NumberColumn("Curr $", format="%.2f"),
            "Form Rating": st.column_config.NumberColumn("Rating", format="%.1f"),
            "Wet (-5..+5)": st.column_config.NumberColumn("Wet", min_value=-5.0, max_value=5.0, step=0.5, format="%+.1f"),
            "J/T Synergy": st.column_config.NumberColumn("J/T", min_value=-5.0, max_value=5.0, step=0.5, format="%+.1f"),
        },
    )
    st.session_state["race_field_df"] = edited_df

    df_eval, overround, vig_pct = evaluate_active_field(edited_df)
    if not df_eval.empty:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Active Starters", len(df_eval))
        m2.metric("Book / Tote Overround", f"{overround*100:.1f}%", delta=f"Vig: {vig_pct:.1f}%", delta_color="inverse")
        m3.metric("🔥 Value Win Plays", int(df_eval["Signal"].str.contains("VALUE").sum()))
        m4.metric("Top Runner EV", f"{df_eval['EV %'].max():+.2f}%")

        st.dataframe(df_eval.drop(columns=["_p_ple"]), use_container_width=True, hide_index=True)

# =====================================================================
# MODE 2: HARVILLE TRIFECTA & EXACTA MATRIX
# =====================================================================
elif mode == "2. Harville Trifecta & Exacta Matrix (Box / Standout)":
    st.subheader(f"🎯 {track_name} Race {race_num} — Harville Trifecta & Exacta Pricer")
    df_eval, _, _ = evaluate_active_field(st.session_state["race_field_df"])

    if len(df_eval) < 3:
        st.warning("Need at least 3 active runners in Mode 1 to price Trifectas.")
    else:
        df_by_no = df_eval.sort_values("No").reset_index(drop=True)
        runner_labels = [f"#{int(r.No)} {r.Horse} (PLE {r._p_ple*100:.1f}%)" for r in df_by_no.itertuples(index=False)]
        label_to_idx = {lbl: idx for idx, lbl in enumerate(runner_labels)}
        p_vec = df_by_no["_p_ple"].to_numpy(dtype=float)

        c1, c2, c3 = st.columns(3)
        first_pick = c1.multiselect("1st Place Leg(s)", runner_labels, default=runner_labels[:2])
        second_pick = c2.multiselect("2nd Place Leg(s)", runner_labels, default=runner_labels[:4])
        third_pick = c3.multiselect("3rd Place Leg(s)", runner_labels, default=runner_labels[:5])

        c_b1, c_b2 = st.columns(2)
        total_outlay = c_b1.number_input("Total Trifecta Outlay ($ AUD)", min_value=1.0, value=24.0, step=1.0)
        est_tote_div = c_b2.number_input("Expected / Current Tote Dividend ($ for $1)", min_value=5.0, value=140.0, step=5.0)

        idx1 = [label_to_idx[x] for x in first_pick]
        idx2 = [label_to_idx[x] for x in second_pick]
        idx3 = [label_to_idx[x] for x in third_pick]

        combos = []
        total_prob = 0.0
        for i in idx1:
            for j in idx2:
                if j == i:
                    continue
                for k in idx3:
                    if k == i or k == j:
                        continue
                    pr = harville_trifecta_prob(p_vec, i, j, k)
                    total_prob += pr
                    combos.append({
                        "1st": f"#{int(df_by_no.loc[i, 'No'])} {df_by_no.loc[i, 'Horse']}",
                        "2nd": f"#{int(df_by_no.loc[j, 'No'])} {df_by_no.loc[j, 'Horse']}",
                        "3rd": f"#{int(df_by_no.loc[k, 'No'])} {df_by_no.loc[k, 'Horse']}",
                        "Harville Prob %": round(pr * 100, 3),
                        "Fair $1 Div": f"${(1.0 / max(pr, 1e-6)):,.2f}",
                    })

        num_combos = len(combos)
        if num_combos == 0:
            st.info("Select distinct runners across 1st, 2nd, and 3rd legs to generate combinations.")
        else:
            flexi_pct = (total_outlay / num_combos) * 100.0
            fair_ticket_price = 1.0 / max(total_prob, 1e-6)
            expected_return = (total_outlay / num_combos) * est_tote_div * total_prob
            tri_ev = ((expected_return - total_outlay) / total_outlay) * 100.0

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Combinations", num_combos, delta=f"Flexi: {flexi_pct:.1f}%")
            m2.metric("Ticket Hit Prob", f"{total_prob*100:.2f}%")
            m3.metric("Break-Even Tote Div", f"${fair_ticket_price:,.2f}")
            m4.metric("Est. Ticket EV", f"{tri_ev:+.1f}%")

            df_combos = pd.DataFrame(combos).sort_values("Harville Prob %", ascending=False).reset_index(drop=True)
            st.dataframe(df_combos.head(30), use_container_width=True, hide_index=True)

# =====================================================================
# MODE 3: TRACK, BARRIER & JOCKEY-TRAINER LAB
# =====================================================================
elif mode == "3. Track, Barrier & Jockey-Trainer Lab":
    st.subheader("🔬 Single-Runner Deep Dive & Fluc Sensitivity")
    df_field = st.session_state["race_field_df"]
    active_names = df_field[df_field["Active"] == True]["Horse"].tolist()
    if not active_names:
        st.warning("No active runners available.")
    else:
        sel_horse = st.selectbox("Select Runner", active_names)
        row = df_field[df_field["Horse"] == sel_horse].iloc[0]

        c1, c2 = st.columns(2)
        with c1:
            sim_curr_odds = st.slider("Simulated Current Odds ($)", 1.20, 51.0, float(row["Curr Odds"]), 0.10)
            sim_rating = st.slider("Custom Form Rating", 60.0, 105.0, float(row["Form Rating"]), 0.5)
        with c2:
            sim_wet = st.slider("Wet Track Affinity (-5 to +5)", -5.0, 5.0, float(row["Wet (-5..+5)"]), 0.5)
            sim_jt = st.slider("Jockey-Trainer Pairing Boost", -5.0, 5.0, float(row["J/T Synergy"]), 0.5)

        sim_df = df_field.copy()
        idx_target = sim_df[sim_df["Horse"] == sel_horse].index[0]
        sim_df.loc[idx_target, "Curr Odds"] = sim_curr_odds
        sim_df.loc[idx_target, "Form Rating"] = sim_rating
        sim_df.loc[idx_target, "Wet (-5..+5)"] = sim_wet
        sim_df.loc[idx_target, "J/T Synergy"] = sim_jt

        res_sim, _, _ = evaluate_active_field(sim_df)
        h_res = res_sim[res_sim["Horse"] == sel_horse].iloc[0]

        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Simulated Odds", f"${h_res['Curr Odds']:.2f}")
        m2.metric("PLE Fair Odds", f"${h_res['PLE Fair Odds']:.2f}")
        m3.metric("PLE Win %", f"{h_res['PLE Win %']:.1f}%", delta=f"Mkt: {h_res['Market %']:.1f}%")
        m4.metric("Simulated EV", f"{h_res['EV %']:+.2f}%", delta=h_res["Signal"])

# =====================================================================
# MODE 4: LOCK RESULTS & MODEL CALIBRATION LOG
# =====================================================================
elif mode == "4. Lock Results & Model Calibration Log":
    st.subheader("💾 Lock Race Results & Track PLE vs Market Accuracy")
    st.markdown(
        "Log completed race results below to commit permanently to `racing_live_results.csv` on GitHub "
        "and track whether your **PLE Win %** and **Value Win** flags beat starting prices."
    )

    with st.form("lock_race_form"):
        c1, c2, c3 = st.columns(3)
        r_date = c1.date_input("Race Date", value=date.today())
        r_track = c2.text_input("Track", value=track_name)
        r_num = c3.number_input("Race Number", min_value=1, max_value=12, value=int(race_num))

        c4, c5, c6 = st.columns(3)
        winner_name = c4.text_input("1st Place Winner", value="Via Sistina")
        sp_odds = c5.number_input("Starting Price / Tote Win ($)", min_value=1.05, value=3.90, step=0.05)
        tri_div = c6.number_input("Actual Trifecta Dividend ($1)", min_value=0.0, value=164.50, step=1.0)

        submitted = st.form_submit_button("🔒 Lock Race Result to GitHub", type="primary")
        if submitted and winner_name.strip():
            new_entry = pd.DataFrame([{
                "date": str(r_date),
                "track": r_track.strip(),
                "race": int(r_num),
                "condition": track_cond,
                "winner": winner_name.strip(),
                "sp_odds": float(sp_odds),
                "trifecta_div": float(tri_div),
            }])
            existing = pd.read_csv(LIVE_RESULTS_FILE) if os.path.exists(LIVE_RESULTS_FILE) else pd.DataFrame()
            combined = pd.concat([existing, new_entry], ignore_index=True).drop_duplicates(
                subset=["date", "track", "race"], keep="last"
            )
            combined.to_csv(LIVE_RESULTS_FILE, index=False)
            ok, msg = push_csv_to_github(
                LIVE_RESULTS_FILE,
                combined.to_csv(index=False),
                f"Lock {r_track} R{int(r_num)} result ({winner_name.strip()})",
            )
            if ok:
                st.success(f"✅ {msg}")
            else:
                st.info(f"✅ Saved locally! ({msg})")

    if os.path.exists(LIVE_RESULTS_FILE):
        st.subheader("📊 Locked Race History")
        st.dataframe(pd.read_csv(LIVE_RESULTS_FILE).tail(30), use_container_width=True, hide_index=True)
