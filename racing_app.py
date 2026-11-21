import base64
import json
import math
import os
import re
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Nilovea Racing — Form & Value",
    page_icon="🐎",
    layout="wide",
)

LIVE_RESULTS_FILE = "racing_live_results.csv"
INGESTED_LOG_FILE = "racing_ingested_history.csv"
MODEL_WEIGHTS_FILE = "racing_model_weights.json"

METRO_TRACKS_BY_STATE = {
    "NSW": [
        "Royal Randwick",
        "Rosehill Gardens",
        "Warwick Farm",
        "Canterbury",
        "Wyong",
        "Gosford",
        "Broadmeadow (Newcastle)",
        "Kembla Grange",
        "Hawkesbury",
    ],
    "VIC": [
        "Flemington",
        "Caulfield",
        "Moonee Valley",
        "Sandown",
        "Cranbourne",
        "Pakenham",
        "Mornington",
        "Ballarat",
        "Bendigo",
        "Geelong",
    ],
    "QLD": [
        "Eagle Farm",
        "Doomben",
        "Sunshine Coast",
        "Gold Coast",
    ],
    "SA": [
        "Morphettville",
        "Morphettville Parks",
        "Murray Bridge",
        "Gawler",
        "Balaklava",
        "Oakbank",
        "Strathalbyn",
        "Port Lincoln",
    ],
    "WA": [
        "Ascot",
        "Belmont Park",
        "Pinjarra",
        "Bunbury",
        "Northam",
        "York",
        "Geraldton",
        "Albany",
        "Kalgoorlie",
    ],
}

DEFAULT_ENGINE_CFG = {
    "form_weights": [3.0, 2.2, 1.6, 1.2, 0.8, 0.5],
    "weight_base": 55.0,
    "weight_coef": 0.45,
    "barrier_center": 5.0,
    "barrier_coef": -0.15,
    "temp": 8.0,
    "market_blend": 0.45,
}


def load_engine_cfg(path: str = MODEL_WEIGHTS_FILE) -> dict:
    cfg = dict(DEFAULT_ENGINE_CFG)
    p = Path(path)
    if p.is_file():
        try:
            loaded = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                cfg.update(loaded)
        except Exception:
            pass
    return cfg


def push_csv_to_github(file_path: str, csv_content: str, commit_msg: str) -> tuple[bool, str]:
    token = st.secrets.get("GITHUB_TOKEN", None) if hasattr(st, "secrets") else None
    repo = (
        st.secrets.get("GITHUB_REPO", "g3ffr0-netizen/nfl-unicorn")
        if hasattr(st, "secrets")
        else "g3ffr0-netizen/nfl-unicorn"
    )
    if not token:
        return False, "No `GITHUB_TOKEN` in Streamlit Secrets (saved locally & available for download)."

    api_url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "Nilovea-Racing-App",
    }

    sha = None
    try:
        req_get = urllib.request.Request(api_url, headers=headers, method="GET")
        with urllib.request.urlopen(req_get, timeout=10) as resp:
            existing_data = json.loads(resp.read().decode("utf-8"))
            sha = existing_data.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            return False, f"GitHub lookup error ({e.code}): {e.reason}"
    except Exception as e:
        return False, f"GitHub connection error: {e}"

    payload = {
        "message": commit_msg,
        "content": base64.b64encode(csv_content.encode("utf-8")).decode("utf-8"),
        "branch": "main",
    }
    if sha:
        payload["sha"] = sha

    try:
        req_put = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="PUT",
        )
        with urllib.request.urlopen(req_put, timeout=15) as resp:
            if resp.status in (200, 201):
                return True, f"Synced `{file_path}` to `{repo}`."
            return False, f"Unexpected GitHub response status: {resp.status}"
    except Exception as e:
        return False, f"GitHub sync error: {e}"


def append_and_persist_csv(file_path: str, new_rows_df: pd.DataFrame, commit_msg: str) -> tuple[pd.DataFrame, bool, str]:
    if os.path.exists(file_path):
        try:
            existing = pd.read_csv(file_path)
            combined = pd.concat([existing, new_rows_df], ignore_index=True)
        except Exception:
            combined = new_rows_df
    else:
        combined = new_rows_df

    csv_str = combined.to_csv(index=False)
    with open(file_path, "w", encoding="utf-8") as fh:
        fh.write(csv_str)

    ok, msg = push_csv_to_github(file_path, csv_str, commit_msg)
    return combined, ok, msg


def count_preloaded_data() -> int:
    total = 0
    candidates = [
        Path(LIVE_RESULTS_FILE),
        Path(INGESTED_LOG_FILE),
        Path("nfl_template_historical.csv"),
    ]
    if Path("data").exists():
        candidates.extend(sorted(Path("data").rglob("*")))

    seen: set[Path] = set()
    for path in candidates:
        resolved = path.resolve() if path.exists() else path
        if resolved in seen or not path.is_file():
            continue
        seen.add(resolved)
        if path.suffix.lower() == ".csv":
            try:
                total += len(pd.read_csv(path))
            except Exception:
                pass
        elif path.suffix.lower() == ".json":
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(raw, list):
                    total += len(raw)
            except Exception:
                pass
    return total


def normalize_runners_df(df: pd.DataFrame, state: str, track: str, race: str) -> pd.DataFrame:
    alias_map = {}
    for col in df.columns:
        key = str(col).strip().lower()
        if key in {"state"}:
            alias_map[col] = "State"
        elif key in {"track", "venue", "meeting"}:
            alias_map[col] = "Track"
        elif key in {"race", "race_name", "event", "race_label"}:
            alias_map[col] = "Race"
        elif key in {"tab", "no", "num", "number", "runner", "saddle"}:
            alias_map[col] = "TAB"
        elif key in {"horse", "name", "runner_name", "selection"}:
            alias_map[col] = "Horse"
        elif key in {"bp", "barrier", "draw", "gate"}:
            alias_map[col] = "BP"
        elif key in {"weight", "wt", "w", "kg"}:
            alias_map[col] = "Weight"
        elif key in {"form", "last6", "last_6", "l6"}:
            alias_map[col] = "Form"
        elif key in {"odds", "win_odds", "fixed_win", "win_fixed", "fixed", "sp", "price", "market_odds"}:
            alias_map[col] = "Market_Odds"
        elif key in {"rating", "sb_rating", "fr", "score", "base_rating"}:
            alias_map[col] = "Base_Rating"

    out = df.rename(columns=alias_map).copy()
    out["State"] = (
        out["State"].fillna(state).astype(str).str.strip().replace("", state)
        if "State" in out.columns
        else state
    )
    out["Track"] = (
        out["Track"].fillna(track).astype(str).str.strip().replace("", track)
        if "Track" in out.columns
        else track
    )
    out["Race"] = (
        out["Race"].fillna(race).astype(str).str.strip().replace("", race)
        if "Race" in out.columns
        else race
    )

    if "TAB" not in out.columns:
        out["TAB"] = np.arange(1, len(out) + 1)
    if "Horse" not in out.columns:
        out["Horse"] = [f"Runner {i}" for i in range(1, len(out) + 1)]
    if "BP" not in out.columns:
        out["BP"] = 0
    if "Weight" not in out.columns:
        out["Weight"] = 55.0
    if "Form" not in out.columns:
        out["Form"] = ""
    if "Base_Rating" not in out.columns:
        out["Base_Rating"] = 80.0
    if "Market_Odds" not in out.columns:
        out["Market_Odds"] = 10.0

    out["TAB"] = pd.to_numeric(out["TAB"], errors="coerce").fillna(0).astype(int)
    out["BP"] = pd.to_numeric(out["BP"], errors="coerce").fillna(0).astype(int)
    out["Weight"] = pd.to_numeric(out["Weight"], errors="coerce").fillna(55.0)
    out["Base_Rating"] = pd.to_numeric(out["Base_Rating"], errors="coerce").fillna(80.0)
    out["Market_Odds"] = pd.to_numeric(out["Market_Odds"], errors="coerce").fillna(10.0).clip(lower=1.01)
    return out


def parse_form_guide(raw_text: str, state: str, track: str, race: str) -> pd.DataFrame:
    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
    runners: list[dict] = []
    current: dict | None = None
    floats: list[float] = []
    active_race = race

    re_race = re.compile(r"^(?:Race\s+\d+|R\d+)\b.*$", re.IGNORECASE)
    re_head = re.compile(r"^(?:Em\d+\s+)?(\d+)\.\s+([A-Za-z].+?)\s*\((\d+)\)$")
    re_wt = re.compile(r"^W:\s*([\d.]+)\s*kg", re.IGNORECASE)
    re_form = re.compile(r"^F:\s*([0-9a-zA-Z]+)$")
    re_rating = re.compile(r"^(?:SB Rating|Rating)\s+(\d+(?:\.\d+)?)$", re.IGNORECASE)
    stop_markers = ("other rules:", "deductions applied", "mystery bets", "bet type")

    def commit(item: dict | None, nums: list[float]) -> None:
        if not item:
            return
        odds_vals = [n for n in nums if 1.05 <= n <= 300.0]
        item["Market_Odds"] = odds_vals[3] if len(odds_vals) > 3 else (odds_vals[0] if odds_vals else 10.0)
        runners.append(item)

    idx = 0
    while idx < len(lines):
        ln = lines[idx]
        low = ln.lower()
        if any(tok in low for tok in stop_markers):
            break

        if "|" not in ln and re_race.match(ln) and len(ln) <= 60:
            active_race = ln
            idx += 1
            continue

        m_head = re_head.match(ln)
        if m_head:
            next_block = " ".join(lines[idx : idx + 4])
            if "Scratched" in next_block:
                idx += 1
                continue

            commit(current, floats)
            floats = []
            current = {
                "State": state,
                "Track": track,
                "Race": active_race,
                "TAB": int(m_head.group(1)),
                "Horse": re.sub(r"\s+", " ", m_head.group(2)).strip(),
                "BP": int(m_head.group(3)),
                "Weight": 55.0,
                "Form": "",
                "Base_Rating": 80.0,
                "Market_Odds": 10.0,
            }
            idx += 1
            continue

        if current is None:
            idx += 1
            continue

        if m := re_wt.match(ln):
            current["Weight"] = float(m.group(1))
        elif m := re_form.match(ln):
            current["Form"] = m.group(1)
        elif m := re_rating.match(ln):
            current["Base_Rating"] = float(m.group(1))
        else:
            try:
                val = float(ln)
                if math.isfinite(val):
                    floats.append(val)
            except ValueError:
                pass
        idx += 1

    commit(current, floats)
    return pd.DataFrame(runners)


def form_bonus(form_str: str, weights: list[float]) -> float:
    score = 0.0
    digits = [ch for ch in str(form_str) if ch.isdigit()]
    for i, ch in enumerate(digits[:6]):
        pos = int(ch)
        w = weights[i] if i < len(weights) else 0.5
        if pos == 1:
            score += 4.0 * w
        elif pos == 2:
            score += 2.2 * w
        elif pos == 3:
            score += 1.2 * w
        elif pos == 4:
            score += 0.4 * w
    return score


def evaluate_race(
    df: pd.DataFrame,
    min_edge_pct: float,
    temp: float,
    market_blend: float,
    cfg: dict,
) -> pd.DataFrame:
    out = df.copy()
    form_weights = cfg.get("form_weights", DEFAULT_ENGINE_CFG["form_weights"])
    weight_base = float(cfg.get("weight_base", DEFAULT_ENGINE_CFG["weight_base"]))
    weight_coef = float(cfg.get("weight_coef", DEFAULT_ENGINE_CFG["weight_coef"]))
    barrier_center = float(cfg.get("barrier_center", DEFAULT_ENGINE_CFG["barrier_center"]))
    barrier_coef = float(cfg.get("barrier_coef", DEFAULT_ENGINE_CFG["barrier_coef"]))

    form_adj = out["Form"].apply(lambda f: form_bonus(f, form_weights))
    weight_adj = (weight_base - out["Weight"]) * weight_coef
    barrier_adj = np.where(out["BP"] > 0, (out["BP"] - barrier_center) * barrier_coef, 0.0)

    out["True_Rating"] = (out["Base_Rating"] + form_adj + weight_adj + barrier_adj).round(2)

    scaled = (out["True_Rating"] - out["True_Rating"].max()) / max(temp, 0.5)
    exp_vals = np.exp(scaled)
    model_probs = exp_vals / exp_vals.sum()

    inv_odds = 1.0 / out["Market_Odds"].clip(lower=1.01)
    mkt_probs = inv_odds / inv_odds.sum()

    blend = float(np.clip(market_blend, 0.0, 1.0))
    probs = (1.0 - blend) * model_probs + blend * mkt_probs
    probs = probs / probs.sum()

    out["Win_Prob_%"] = (probs * 100.0).round(2)
    out["Fair_Odds"] = np.where(probs > 1e-6, (1.0 / probs).round(2), 999.0)
    out["Edge_%"] = ((probs * out["Market_Odds"] - 1.0) * 100.0).round(2)
    out["Value"] = np.where(out["Edge_%"] >= min_edge_pct, "VALUE", "")

    return out.sort_values("Win_Prob_%", ascending=False).reset_index(drop=True)


if "field_store" not in st.session_state:
    st.session_state["field_store"] = pd.DataFrame()

engine_cfg = load_engine_cfg()
preloaded_rows = count_preloaded_data()

st.title("Nilovea Racing — Form & Value")
st.caption("Select state & race-day tracks, drop in form or CSV/JSON per race, and spot value vs. market odds.")

with st.sidebar:
    st.subheader("Race Day Tracks")
    selected_state = st.selectbox("State", options=list(METRO_TRACKS_BY_STATE.keys()), index=0)
    state_tracks = METRO_TRACKS_BY_STATE[selected_state]
    active_tracks = st.multiselect(
        "Today's Track(s)",
        options=state_tracks,
        default=[state_tracks[0]],
    )
    target_track = st.selectbox(
        "Target Track for New Form",
        options=active_tracks if active_tracks else state_tracks,
        index=0,
    )
    target_race = st.selectbox(
        "Target Race",
        options=[f"R{i}" for i in range(1, 13)],
        index=6,
    )
    st.divider()
    st.subheader("Calibrated Engine & Data")
    st.metric("Preloaded Rows", preloaded_rows)
    min_edge_pct = st.slider("Min Value Edge (%)", 0.0, 30.0, 5.0, 0.5)
    temp = st.slider("Rating Spread (Temp)", 2.0, 15.0, float(engine_cfg["temp"]), 0.5)
    market_blend = st.slider(
        "Market Blend Shrinkage",
        0.0,
        0.85,
        float(engine_cfg["market_blend"]),
        0.05,
    )
    if st.button("Clear Session Races"):
        st.session_state["field_store"] = pd.DataFrame()
        st.rerun()

col_upload, col_paste = st.columns([1, 1.5])
with col_upload:
    uploaded = st.file_uploader(f"Upload CSV / JSON → {target_track} {target_race}", type=["csv", "json"])
with col_paste:
    pasted = st.text_area(
        f"Paste form text → {target_track} {target_race}",
        height=130,
        placeholder="5. Dirtballer (6)\nW: 57.5kg\nF: 11x...",
    )

incoming = pd.DataFrame()
if uploaded is not None:
    if uploaded.name.lower().endswith(".csv"):
        incoming = normalize_runners_df(pd.read_csv(uploaded), selected_state, target_track, target_race)
    else:
        raw_json = json.loads(uploaded.getvalue().decode("utf-8"))
        if isinstance(raw_json, list):
            incoming = normalize_runners_df(pd.DataFrame(raw_json), selected_state, target_track, target_race)
elif pasted.strip():
    parsed = parse_form_guide(pasted, selected_state, target_track, target_race)
    if not parsed.empty:
        incoming = normalize_runners_df(parsed, selected_state, target_track, target_race)

if not incoming.empty:
    if st.session_state["field_store"].empty:
        st.session_state["field_store"] = incoming.drop_duplicates(subset=["State", "Track", "Race", "TAB", "Horse"])
    else:
        combined_store = pd.concat([st.session_state["field_store"], incoming], ignore_index=True)
        st.session_state["field_store"] = combined_store.drop_duplicates(
            subset=["State", "Track", "Race", "TAB", "Horse"], keep="last"
        )

store = st.session_state["field_store"]
if store.empty:
    st.info(f"Pick {target_track} & {target_race} in the sidebar, then paste form text or upload a CSV/JSON.")
else:
    race_options = [
        f"{r.State} | {r.Track} | {r.Race}"
        for r in store[["State", "Track", "Race"]].drop_duplicates().itertuples(index=False)
    ]
    default_key = f"{selected_state} | {target_track} | {target_race}"
    default_idx = race_options.index(default_key) if default_key in race_options else 0
    chosen_race_key = st.selectbox("View Loaded Race", options=race_options, index=default_idx)

    c_state, c_track, c_race = [part.strip() for part in chosen_race_key.split("|", 2)]
    race_df = store[
        (store["State"] == c_state) & (store["Track"] == c_track) & (store["Race"] == c_race)
    ].copy()

    board = evaluate_race(
        race_df,
        min_edge_pct=min_edge_pct,
        temp=temp,
        market_blend=market_blend,
        cfg=engine_cfg,
    )
    value_picks = board[board["Value"] == "VALUE"]

    m1, m2, m3 = st.columns(3)
    m1.metric("Top Win Prob", f"#{board.loc[0, 'TAB']} {board.loc[0, 'Horse']}", f"{board.loc[0, 'Win_Prob_%']}%")
    m2.metric("Highest Rating", f"{board.loc[0, 'True_Rating']}", f"Fair ${board.loc[0, 'Fair_Odds']}")
    m3.metric("Value Bets", f"{len(value_picks)}", f"Edge >= {min_edge_pct:.1f}%")

    show_cols = [
        "Value",
        "Track",
        "Race",
        "TAB",
        "Horse",
        "BP",
        "Weight",
        "True_Rating",
        "Win_Prob_%",
        "Fair_Odds",
        "Market_Odds",
        "Edge_%",
    ]
    st.dataframe(board[show_cols], use_container_width=True, hide_index=True)

    if not value_picks.empty:
        st.success(
            f"Value bets ({chosen_race_key}): "
            + ", ".join(
                f"#{r['TAB']} {r['Horse']} (${r['Market_Odds']:.2f} vs fair ${r['Fair_Odds']:.2f}, +{r['Edge_%']:.1f}%)"
                for _, r in value_picks.iterrows()
            )
        )

    col_save_field, col_log_res = st.columns(2)

    with col_save_field:
        with st.expander("Save Ingested Race Field"):
            st.caption("Saves all evaluated runners for this race to `racing_ingested_history.csv`.")
            if st.button("Save Field Snapshot"):
                snap = board.copy()
                snap["race_date"] = date.today().isoformat()
                ordered_cols = ["race_date"] + [c for c in snap.columns if c != "race_date"]
                snap = snap[ordered_cols]
                combined_snap, ok, msg = append_and_persist_csv(
                    INGESTED_LOG_FILE,
                    snap,
                    f"Ingest field: {chosen_race_key} ({date.today().isoformat()})",
                )
                st.info(msg if not ok else f"Saved & {msg}")
                st.download_button(
                    "Download Ingested History CSV",
                    data=combined_snap.to_csv(index=False).encode("utf-8"),
                    file_name=INGESTED_LOG_FILE,
                    mime="text/csv",
                )

    with col_log_res:
        with st.expander("Log Race Result"):
            race_label = st.text_input("Race / Meeting", value=f"{date.today().isoformat()} {chosen_race_key}")
            winner_tab = st.number_input("Winner TAB", min_value=1, max_value=30, value=int(board.loc[0, "TAB"]))
            if st.button("Save Winner to CSV"):
                row_df = pd.DataFrame(
                    [{"date": date.today().isoformat(), "race": race_label, "winner_tab": int(winner_tab)}]
                )
                combined_res, ok, msg = append_and_persist_csv(
                    LIVE_RESULTS_FILE,
                    row_df,
                    f"Log result: {race_label}",
                )
                st.info(msg if not ok else f"Saved & {msg}")
                st.download_button(
                    "Download Results CSV",
                    data=combined_res.to_csv(index=False).encode("utf-8"),
                    file_name=LIVE_RESULTS_FILE,
                    mime="text/csv",
                )
