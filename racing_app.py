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


def push_csv_to_github(file_path: str, csv_content: str, commit_msg: str) -> tuple[bool, str]:
    """Commits updated racing results straight back into GitHub when GITHUB_TOKEN is configured."""
    token = st.secrets.get("GITHUB_TOKEN", None) if hasattr(st, "secrets") else None
    repo = (
        st.secrets.get("GITHUB_REPO", "g3ffr0-netizen/nfl-unicorn")
        if hasattr(st, "secrets")
        else "g3ffr0-netizen/nfl-unicorn"
    )
    if not token:
        return False, "No `GITHUB_TOKEN` found in Streamlit Secrets (saved locally & downloadable below)."

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


def count_preloaded_data() -> int:
    """Count rows available from existing CSV/JSON files in the repo/data folders."""
    total = 0
    candidates = [Path(LIVE_RESULTS_FILE), Path("nfl_template_historical.csv")]
    if Path("data").exists():
        candidates.extend(sorted(Path("data").rglob("*")))

    for path in candidates:
        if not path.is_file():
            continue
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


def normalize_runners_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names safely so uploads or pasted data never fail with KeyError: 'TAB'."""
    alias_map = {}
    for col in df.columns:
        key = str(col).strip().lower()
        if key in {"tab", "no", "num", "number", "runner", "saddle"}:
            alias_map[col] = "TAB"
        elif key in {"horse", "name", "runner_name", "selection"}:
            alias_map[col] = "Horse"
        elif key in {"bp", "barrier", "draw", "gate"}:
            alias_map[col] = "BP"
        elif key in {"weight", "wt", "w", "kg"}:
            alias_map[col] = "Weight"
        elif key in {"form", "last6", "last_6", "l6"}:
            alias_map[col] = "Form"
        elif key in {"odds", "win_odds", "fixed_win", "fixed", "sp", "price", "market_odds"}:
            alias_map[col] = "Market_Odds"
        elif key in {"rating", "sb_rating", "fr", "score", "base_rating"}:
            alias_map[col] = "Base_Rating"

    out = df.rename(columns=alias_map).copy()
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


def parse_form_guide(raw_text: str) -> pd.DataFrame:
    """Parse pasted form guide runner blocks into structured rows."""
    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
    runners: list[dict] = []
    current: dict | None = None
    floats: list[float] = []

    re_head = re.compile(r"^(\d+)\.\s+([^(]+?)(?:\s*\((\d+)\))?$")
    re_wt = re.compile(r"^W:\s*([\d.]+)\s*kg", re.IGNORECASE)
    re_form = re.compile(r"^F:\s*([0-9a-zA-Z]+)$")
    re_rating = re.compile(r"^(?:SB Rating|Rating)\s+(\d+(?:\.\d+)?)$", re.IGNORECASE)

    def commit(item: dict | None, nums: list[float]) -> None:
        if not item:
            return
        odds_vals = [n for n in nums if 1.05 <= n <= 300.0]
        item["Market_Odds"] = odds_vals[3] if len(odds_vals) > 3 else (odds_vals[0] if odds_vals else 10.0)
        runners.append(item)

    for ln in lines:
        if m := re_head.match(ln):
            commit(current, floats)
            floats = []
            current = {
                "TAB": int(m.group(1)),
                "Horse": m.group(2).strip(),
                "BP": int(m.group(3)) if m.group(3) else 0,
                "Weight": 55.0,
                "Form": "",
                "Base_Rating": 80.0,
                "Market_Odds": 10.0,
            }
            continue

        if current is None:
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

    commit(current, floats)
    return pd.DataFrame(runners)


def form_bonus(form_str: str) -> float:
    weights = [3.0, 2.2, 1.6, 1.2, 0.8, 0.5]
    score = 0.0
    digits = [ch for ch in str(form_str) if ch.isdigit()]
    for idx, ch in enumerate(digits[:6]):
        pos = int(ch)
        w = weights[idx] if idx < len(weights) else 0.5
        if pos == 1:
            score += 4.0 * w
        elif pos == 2:
            score += 2.2 * w
        elif pos == 3:
            score += 1.2 * w
        elif pos == 4:
            score += 0.4 * w
    return score


def evaluate_field(df: pd.DataFrame, min_edge_pct: float, temp: float) -> pd.DataFrame:
    out = df.copy()
    form_adj = out["Form"].apply(form_bonus)
    weight_adj = (55.0 - out["Weight"]) * 0.6
    barrier_adj = np.where(out["BP"] > 0, -(out["BP"] - 5.0) * 0.2, 0.0)

    out["True_Rating"] = (out["Base_Rating"] + form_adj + weight_adj + barrier_adj).round(2)

    scaled = (out["True_Rating"] - out["True_Rating"].max()) / max(temp, 0.5)
    exp_vals = np.exp(scaled)
    probs = exp_vals / exp_vals.sum()

    out["Win_Prob_%"] = (probs * 100.0).round(2)
    out["Fair_Odds"] = np.where(probs > 1e-6, (1.0 / probs).round(2), 999.0)
    out["Edge_%"] = ((probs * out["Market_Odds"] - 1.0) * 100.0).round(2)
    out["Value"] = np.where(out["Edge_%"] >= min_edge_pct, "VALUE", "")

    return out.sort_values("Win_Prob_%", ascending=False).reset_index(drop=True)


st.title("Nilovea Racing — Form & Value")
st.caption("Single-screen form parser, true ratings, win probabilities, and value edge vs. market odds.")

preloaded_rows = count_preloaded_data()

with st.sidebar:
    st.subheader("Data & Value")
    st.metric("Preloaded Rows", preloaded_rows)
    min_edge_pct = st.slider("Min Value Edge (%)", 0.0, 30.0, 5.0, 0.5)
    temp = st.slider("Rating Spread (Temp)", 2.0, 15.0, 6.0, 0.5)

col_upload, col_paste = st.columns([1, 1.5])
with col_upload:
    uploaded = st.file_uploader("Upload CSV or JSON", type=["csv", "json"])
with col_paste:
    pasted = st.text_area(
        "Paste form guide text",
        height=140,
        placeholder="1. Gringotts (NZ) (2)\nW: 61.0kg\nF: 4x3573...",
    )

runners = pd.DataFrame()
if uploaded is not None:
    if uploaded.name.lower().endswith(".csv"):
        runners = normalize_runners_df(pd.read_csv(uploaded))
    else:
        raw_json = json.loads(uploaded.getvalue().decode("utf-8"))
        if isinstance(raw_json, list):
            runners = normalize_runners_df(pd.DataFrame(raw_json))
elif pasted.strip():
    parsed = parse_form_guide(pasted)
    if not parsed.empty:
        runners = normalize_runners_df(parsed)

if runners.empty:
    st.info("Paste form guide text or upload a CSV/JSON file above to run ratings, win probabilities, and value checks.")
else:
    board = evaluate_field(runners, min_edge_pct=min_edge_pct, temp=temp)
    value_picks = board[board["Value"] == "VALUE"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Top Win Prob", f"#{board.loc[0, 'TAB']} {board.loc[0, 'Horse']}", f"{board.loc[0, 'Win_Prob_%']}%")
    c2.metric("Highest Rating", f"{board.loc[0, 'True_Rating']}", f"Fair ${board.loc[0, 'Fair_Odds']}")
    c3.metric("Value Bets", f"{len(value_picks)}", f"Edge >= {min_edge_pct:.1f}%")

    show_cols = [
        "Value",
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
            "Value bets: "
            + ", ".join(
                f"#{r['TAB']} {r['Horse']} (${r['Market_Odds']:.2f} vs fair ${r['Fair_Odds']:.2f}, +{r['Edge_%']:.1f}%)"
                for _, r in value_picks.iterrows()
            )
        )

    with st.expander("Log Race Result"):
        race_label = st.text_input("Race / Meeting", value=f"{date.today().isoformat()} Race")
        winner_tab = st.number_input("Winner TAB", min_value=1, max_value=30, value=int(board.loc[0, "TAB"]))
        if st.button("Save Winner to CSV"):
            row_df = pd.DataFrame([{"date": date.today().isoformat(), "race": race_label, "winner_tab": int(winner_tab)}])
            if os.path.exists(LIVE_RESULTS_FILE):
                existing = pd.read_csv(LIVE_RESULTS_FILE)
                combined = pd.concat([existing, row_df], ignore_index=True)
            else:
                combined = row_df
            csv_str = combined.to_csv(index=False)
            with open(LIVE_RESULTS_FILE, "w", encoding="utf-8") as fh:
                fh.write(csv_str)
            ok, msg = push_csv_to_github(LIVE_RESULTS_FILE, csv_str, f"Log result: {race_label}")
            st.info(msg if not ok else f"Saved & {msg}")
