import json
import re
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

INGESTED_FILE = Path("racing_ingested_history.csv")
RESULTS_FILE = Path("racing_live_results.csv")
WEIGHTS_FILE = Path("racing_model_weights.json")

DEFAULT_CFG = {
    "form_weights": [3.0, 2.2, 1.6, 1.2, 0.8, 0.5],
    "weight_base": 55.0,
    "weight_coef": 0.45,
    "barrier_center": 5.0,
    "barrier_coef": -0.15,
    "temp": 8.0,
    "market_blend": 0.45,
}


def parse_result_key(label: str) -> tuple[str, str, str]:
    # Expected format: "2026-11-21 VIC | Kilmore | R9"
    m = re.match(r"^(\d{4}-\d{2}-\d{2})\s+(.+?)\s*\|\s*(.+?)\s*\|\s*(R\d+)$", str(label).strip())
    if not m:
        return "", "", ""
    return m.group(1), m.group(3).strip(), m.group(4).strip().upper()


def main() -> None:
    cfg = dict(DEFAULT_CFG)
    if WEIGHTS_FILE.is_file():
        try:
            cfg.update(json.loads(WEIGHTS_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass

    if not (INGESTED_FILE.is_file() and RESULTS_FILE.is_file()):
        print("Waiting for both racing_ingested_history.csv and racing_live_results.csv.")
        return

    hist = pd.read_csv(INGESTED_FILE)
    res = pd.read_csv(RESULTS_FILE)
    if hist.empty or res.empty:
        print("Empty history or results file; skipping recalibration.")
        return

    matched_races = []
    for row in res.itertuples(index=False):
        r_date, r_track, r_race = parse_result_key(getattr(row, "race", ""))
        win_tab = int(getattr(row, "winner_tab", -1))
        if not r_date:
            continue
        sub = hist[
            (hist["race_date"].astype(str) == r_date)
            & (hist["Track"].astype(str).str.strip() == r_track)
            & (hist["Race"].astype(str).str.strip().str.upper() == r_race)
        ].copy()
        if len(sub) >= 4 and (sub["TAB"].astype(int) == win_tab).any():
            matched_races.append((sub, win_tab))

    if len(matched_races) < 10:
        print(f"Only {len(matched_races)} matched races so far (need >= 10 before tuning weights).")
        return

    best_loss = float("inf")
    best_temp = cfg["temp"]
    best_blend = cfg["market_blend"]

    for temp in np.arange(4.0, 13.5, 0.5):
        for blend in np.arange(0.15, 0.80, 0.05):
            total_loss = 0.0
            for sub, win_tab in matched_races:
                ratings = pd.to_numeric(sub["True_Rating"], errors="coerce").fillna(80.0).to_numpy()
                odds = pd.to_numeric(sub["Market_Odds"], errors="coerce").fillna(10.0).clip(lower=1.01).to_numpy()
                tabs = sub["TAB"].astype(int).to_numpy()

                scaled = (ratings - ratings.max()) / temp
                m_probs = np.exp(scaled) / np.exp(scaled).sum()
                mkt_probs = (1.0 / odds) / (1.0 / odds).sum()
                probs = (1.0 - blend) * m_probs + blend * mkt_probs
                probs = probs / probs.sum()

                win_p = float(probs[tabs == win_tab][0])
                total_loss -= np.log(max(win_p, 1e-6))

            avg_loss = total_loss / len(matched_races)
            if avg_loss < best_loss:
                best_loss = avg_loss
                best_temp = round(float(temp), 2)
                best_blend = round(float(blend), 2)

    cfg["temp"] = best_temp
    cfg["market_blend"] = best_blend
    cfg["last_calibrated_utc"] = datetime.now(timezone.utc).isoformat()
    cfg["calibrated_sample_races"] = len(matched_races)
    cfg["avg_log_loss"] = round(best_loss, 4)

    WEIGHTS_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    print(f"Updated {WEIGHTS_FILE}: temp={best_temp}, market_blend={best_blend}, log_loss={best_loss:.4f}")


if __name__ == "__main__":
    main()
