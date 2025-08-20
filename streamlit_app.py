# app.py
# FFL Advisor — Streamlit one-file app (embedded samples, safe for Streamlit Cloud)

import os, io, typing as T
import pandas as pd, numpy as np
import streamlit as st

DEFAULT_URLS = {
    "roster_csv":     "https://YOUR-BUCKET/roster.csv",
    "projections_csv":"https://YOUR-BUCKET/projections.csv",
    "waiver_csv":     "https://YOUR-BUCKET/waiver.csv",
    "defense_csv":    "https://YOUR-BUCKET/defense_vs_pos.csv",
    "news_csv":       "https://YOUR-BUCKET/news_signals.csv"
}

LEAGUE_DEFAULTS = {
    "teams": 10, "ppr": 0, "pass_td": 6, "rush_rec_td": 6,
    "qb_slots": 1, "rb_slots": 2, "wr_slots": 2, "te_slots": 1,
    "flex_slots": 1, "bench_slots": 6,
    "bonus_40plus": 1.0, "bonus_100rush": 2.0, "bonus_100rec": 2.0, "bonus_300pass": 2.0,
}

COLS = {
    "player":["player","name","Player"],
    "pos":["pos","position","Position"],
    "team":["team","Team"],
    "opp":["opp","opponent","Opponent"],
    "proj":["proj","projection","Projected","projected_points","Proj"],
    "status":["inj","status","Injury Status","injury_status"],
    "pct_owned":["owned","percent_owned","PctOwned"],
    "def_rank":["def_rank","dvp","DefenseRank","Opp_Def_Rank"],
    "notes":["notes","Note"],
    "risk":["risk","boom_bust","volatility"],
    "bye":["bye","ByeWeek"],
    "team_def":["team_def","DST","DefenseTeam"],
}

# --------- embedded sample CSVs ---------
def _df(text): return pd.read_csv(io.StringIO(text))

SAMPLES = {
  "roster": _df("""player,pos,team,opp,status,bye
Patrick Mahomes,QB,KC,BAL,Healthy,10
Bijan Robinson,RB,ATL,TB,Healthy,12
Nick Chubb,RB,CLE,CIN,Questionable,10
Justin Jefferson,WR,MIN,GB,Healthy,6
Amon-Ra St. Brown,WR,DET,CHI,Healthy,5
Travis Kelce,TE,KC,BAL,Healthy,10
James Conner,RB,ARI,LAR,Healthy,14
Deebo Samuel,WR,SF,SEA,Healthy,9
Dallas Goedert,TE,PHI,DAL,Healthy,10
49ers D/ST,DEF,SF,SEA,Healthy,9
"""),
  "projections": _df("""player,pos,team,opp,proj,status
Patrick Mahomes,QB,KC,BAL,24.8,Healthy
Bijan Robinson,RB,ATL,TB,16.5,Healthy
Nick Chubb,RB,CLE,CIN,13.9,Questionable
Justin Jefferson,WR,MIN,GB,19.2,Healthy
Amon-Ra St. Brown,WR,DET,CHI,17.6,Healthy
Travis Kelce,TE,KC,BAL,15.3,Healthy
James Conner,RB,ARI,LAR,12.1,Healthy
Deebo Samuel,WR,SF,SEA,14.7,Healthy
Dallas Goedert,TE
