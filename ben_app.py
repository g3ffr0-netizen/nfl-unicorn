# =====================================================================
# MODE 1: WEEK AHEAD SLATE SCANNER (WITH QB / KEY INJURY ADJUSTMENTS)
# =====================================================================
if mode == "1. Week Ahead Slate Scanner (Spread + O/U + PLE)":
    st.subheader("⚡ Week Ahead Slate Scanner (`Team 1, Team 2, Spread, O/U, Injury_Adj_T1`)")
    st.caption(
        "Optional 5th column = **Net Injury Point Adjustment for Team 1** "
        "(e.g. `-5.5` if Team 1's starting QB is out; `+5.5` if Team 2's starting QB is out; `0` if healthy)."
    )

    c_up, c_home = st.columns([2, 1])
    with c_up:
        up_txt = st.file_uploader("Drop `todays nfl games.txt` or weekly slate `.csv`", type=["txt", "csv"])
    with c_home:
        team_1_is_home = st.radio(
            "Home Team Order",
            [True, False],
            format_func=lambda x: "Team 1 is Home" if x else "Team 1 is Away (Team 2 Home)",
        )

    default_slate = """Chargers, Ravens, 3.5, 45.5, 0.0
Patriots, Lions, -2.5, 48.5, 0.0
Chiefs, Falcons, -7.5, 47.5, 0.0
Texans, Browns, -1.5, 41.5, 0.0
Vikings, Packers, -2.5, 45.5, 0.0
Dolphins, Colts, 1.5, 45.5, 0.0
Panthers, Saints, -3.5, 43.5, 0.0
Bills, Jets, -1.5, 40.5, 0.0
Jaguars, Titans, -1.5, 39.5, 0.0
Rams, Cardinals, -7.5, 48.5, 0.0
Seahawks, Raiders, -2.5, 41.5, 0.0
49ers, Cowboys, -7.5, 47.5, 0.0
Steelers, Bengals, 2.5, 46.5, 0.0"""

    slate_text = up_txt.read().decode("utf-8") if up_txt is not None else st.text_area("Or paste week ahead games:", value=default_slate, height=210)

    if slate_text.strip():
        parsed_games = []
        for line in slate_text.strip().splitlines():
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 3:
                continue
            try:
                sp1 = float(parts[2])
            except ValueError:
                continue
            ou_line = float(parts[3]) if len(parts) >= 4 and parts[3] != "" else np.nan
            inj_adj = float(parts[4]) if len(parts) >= 5 and parts[4] != "" else 0.0
            parsed_games.append({
                "Team 1": parts[0],
                "Team 2": parts[1],
                "Spread (T1)": sp1,
                "O/U Line": ou_line,
                "T1 Injury Pts": inj_adj,
            })

        if parsed_games:
            st.markdown("#### 🏥 Interactive QB & Key Injury Override Table")
            st.caption("Edit **T1 Injury Pts** directly below (`-6.0` = T1 backup QB, `+6.0` = T2 backup QB) to recalculate live:")
            edited_slate = st.data_editor(
                pd.DataFrame(parsed_games),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Team 1": st.column_config.TextColumn(disabled=True),
                    "Team 2": st.column_config.TextColumn(disabled=True),
                    "Spread (T1)": st.column_config.NumberColumn(format="%.1f"),
                    "O/U Line": st.column_config.NumberColumn(format="%.1f"),
                    "T1 Injury Pts": st.column_config.NumberColumn(
                        min_value=-14.0,
                        max_value=14.0,
                        step=0.5,
                        format="%+.1f",
                        help="Negative = Team 1 hurt by injuries; Positive = Team 2 hurt by injuries",
                    ),
                },
            )

            rows = []
            for g in edited_slate.itertuples(index=False):
                raw_t1, raw_t2 = g[0], g[1]
                sp1 = float(g[2])
                ou_line = None if pd.isna(g[3]) else float(g[3])
                inj_adj_t1 = float(g[4]) if pd.notna(g[4]) else 0.0

                t1, t2 = norm_team(raw_t1), norm_team(raw_t2)
                _, _, base_fair_sp1, base_pred_tot, div_game = predict_game_spreadspoke(
                    t1, t2, profiles, team_1_is_home=team_1_is_home
                )

                # Apply QB / Key Injury adjustment (positive inj_adj_t1 makes T1 stronger / more negative spread)
                fair_sp1 = round(base_fair_sp1 - inj_adj_t1, 1)
                pred_tot = round(base_pred_tot - (0.35 * abs(inj_adj_t1)), 1)

                cover_margin_1 = (-fair_sp1) - (-sp1)
                p_raw_1 = spread_to_win_prob(-cover_margin_1)
                p_hat_1 = ple_calibrate_prob(0.50, p_raw_1, shrinkage_lambda)
                p_hat_2 = 1.0 - p_hat_1

                dec_line = 1.909
                ev_1, ev_2 = (p_hat_1 * dec_line) - 1.0, (p_hat_2 * dec_line) - 1.0
                best_ev = max(ev_1, ev_2)

                if ev_1 >= min_ev and ev_1 >= ev_2:
                    sig, pick, stk = "🔥 VALUE BET", f"{raw_t1} ({sp1:+.1f})", bankroll * kelly_fraction(p_hat_1, dec_line, kelly_mult)
                elif ev_2 >= min_ev and ev_2 > ev_1:
                    sig, pick, stk = "🔥 VALUE BET", f"{raw_t2} ({-sp1:+.1f})", bankroll * kelly_fraction(p_hat_2, dec_line, kelly_mult)
                else:
                    sig, pick, stk = "⚪ PASS", "—", 0.0

                ou_pick = "—"
                if ou_line is not None:
                    diff_ou = pred_tot - ou_line
                    if abs(diff_ou) >= 2.0:
                        ou_pick = f"{'OVER' if diff_ou > 0 else 'UNDER'} {ou_line} (Model: {pred_tot})"
                    else:
                        ou_pick = f"Lean {'Over' if diff_ou > 0 else 'Under'} ({pred_tot})"

                inj_badge = f" ({inj_adj_t1:+.1f} inj)" if inj_adj_t1 != 0 else ""
                rows.append({
                    "Matchup": f"{raw_t1} vs {raw_t2}" + (" 🏟️DIV" if div_game else ""),
                    "Spread Line": f"{raw_t1} {sp1:+.1f}",
                    "Model Fair": f"{raw_t1} {fair_sp1:+.1f}{inj_badge}",
                    "Signal": sig,
                    "Best Spread Pick": pick,
                    "PLE Cover %": round(max(p_hat_1, p_hat_2) * 100, 1),
                    "EV @ -110": round(best_ev * 100, 2),
                    "Kelly Stake": f"${stk:,.2f}",
                    "O/U Model Pick": ou_pick,
                })

            df_out = pd.DataFrame(rows).sort_values("EV @ -110", ascending=False).reset_index(drop=True)
            m1, m2, m3 = st.columns(3)
            m1.metric("Games Scanned", len(df_out))
            m2.metric("🔥 Value Spread Bets", int(df_out["Signal"].str.contains("VALUE").sum()))
            m3.metric("Top Spread EV", f"{df_out['EV @ -110'].max():+.2f}%")
            st.dataframe(df_out, use_container_width=True, hide_index=True)
