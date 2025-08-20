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
Dallas Goedert,TE,PHI,DAL,10.2,Healthy
49ers D/ST,DEF,SF,SEA,7.0,Healthy
Puka Nacua,WR,LAR,ARI,12.4,Healthy
Rachaad White,RB,TB,ATL,11.3,Healthy
Jayden Reed,WR,GB,MIN,11.6,Healthy
Tony Pollard,RB,DAL,PHI,13.5,Healthy
Tee Higgins,WR,CIN,CLE,12.9,Healthy
"""),
  "waiver": _df("""player,pos,team,opp,proj,percent_owned,status
Puka Nacua,WR,LAR,ARI,12.4,72,Healthy
Zach Charbonnet,RB,SEA,SF,8.8,48,Healthy
Tank Dell,WR,HOU,JAX,11.1,55,Healthy
Brock Bowers,TE,LV,DEN,8.9,41,Healthy
Rico Dowdle,RB,DAL,PHI,7.6,22,Healthy
Khalil Shakir,WR,BUF,NE,9.7,38,Healthy
Tyjae Spears,RB,TEN,IND,8.4,36,Healthy
Romeo Doubs,WR,GB,MIN,10.1,47,Healthy
Jameson Williams,WR,DET,CHI,9.9,44,Healthy
Chase Brown,RB,CIN,CLE,7.1,18,Healthy
"""),
  "defense": _df("""pos,team,def_rank
QB,BAL,6
RB,TB,7
WR,GB,10
TE,GB,12
WR,CHI,28
TE,CHI,20
RB,CIN,12
WR,SEA,14
TE,SEA,16
WR,DAL,9
TE,DAL,8
RB,LAR,18
WR,ARI,26
RB,PHI,9
WR,PHI,7
RB,IND,21
WR,NE,15
RB,DEN,14
WR,MIN,20
"""),
  "news": _df("""time,player,team,tag,blurb,source
2025-08-18T14:05:00Z,Bijan Robinson,ATL,role,"Expected heavier red-zone usage this week.",Rotoworld
2025-08-18T15:10:00Z,Nick Chubb,CLE,injury,"Limited in practice; true game-time decision.",Team Beat
2025-08-18T16:40:00Z,Justin Jefferson,MIN,severe,"No limitations expected; trending up.",ESPN
2025-08-19T12:30:00Z,Travis Kelce,KC,injury,"Veteran rest day; full go Sunday.",KC Reporter
2025-08-19T18:15:00Z,Deebo Samuel,SF,role,"Increased slot snaps planned vs SEA.",Local Radio
"""),
}

# --------- helpers ----------
def coalesce_col(df, wanted, default=None):
    for c in wanted:
        if c in df.columns: return df[c]
    lower = {c.lower(): c for c in df.columns}
    for c in wanted:
        if c.lower() in lower: return df[lower[c.lower()]]
    return pd.Series([default]*len(df))

def normalize_columns(df):
    if df is None or len(df)==0: return pd.DataFrame()
    out = pd.DataFrame()
    out["player"]   = coalesce_col(df, COLS["player"], "")
    out["pos"]      = coalesce_col(df, COLS["pos"], "").astype(str).str.upper().str.replace("DST","DEF", regex=False)
    out["team"]     = coalesce_col(df, COLS["team"], "").astype(str).str.upper()
    out["opp"]      = coalesce_col(df, COLS["opp"], "").astype(str).str.upper()
    out["proj"]     = pd.to_numeric(coalesce_col(df, COLS["proj"], 0), errors="coerce").fillna(0.0)
    out["status"]   = coalesce_col(df, COLS["status"], "").astype(str).str.title()
    out["pct_owned"]= pd.to_numeric(coalesce_col(df, COLS["pct_owned"], 0), errors="coerce").fillna(0.0)
    out["def_rank"] = pd.to_numeric(coalesce_col(df, COLS["def_rank"], 16), errors="coerce").fillna(16)
    out["notes"]    = coalesce_col(df, COLS["notes"], "")
    out["risk"]     = pd.to_numeric(coalesce_col(df, COLS["risk"], 0), errors="coerce").fillna(0.0)
    out["bye"]      = pd.to_numeric(coalesce_col(df, COLS["bye"], 0), errors="coerce").fillna(0).astype(int)
    out["team_def"] = coalesce_col(df, COLS["team_def"], "")
    return out

@st.cache_data(ttl=3600)
def fetch_csv(url: str):
    if not url or str(url).startswith("https://YOUR-BUCKET"): return pd.DataFrame()
    try: return pd.read_csv(url)
    except Exception:
        try: return pd.read_csv(url, encoding="latin-1")
        except Exception: return pd.DataFrame()

def adj_for_defense(proj, def_rank, pos):
    if pos=="DEF": return proj
    strength = np.clip((def_rank-16)/16.0, -1, 1)
    return proj*(1+0.10*strength)

def adj_for_status(proj, status):
    s=(status or "").lower()
    if "out" in s: return 0.0
    if "doubt" in s: return proj*0.5
    if "quest" in s: return proj*0.85
    return proj

def flex_ok(pos): return pos in {"RB","WR","TE"}

def compute_value(row, league):
    base=float(row.get("proj",0.0))
    base=adj_for_defense(base, row.get("def_rank",16), row.get("pos",""))
    base=adj_for_status(base, row.get("status",""))
    risk=float(row.get("risk",0.0))
    return max(base + 0.15*risk, 0.0)

def counts(league):
    return {"QB":league["qb_slots"],"RB":league["rb_slots"],"WR":league["wr_slots"],"TE":league["te_slots"],"FLEX":league["flex_slots"]}

def fill_lineup(players, league):
    if players.empty: return players, players
    df=players.copy()
    df["value"]=df.apply(lambda r: compute_value(r,league), axis=1)
    df=df.sort_values("value", ascending=False).reset_index(drop=True)
    need=counts(league); chosen=set()

    def take(pos,n):
        nonlocal chosen
        pool=df[(~df.index.isin(chosen))&(df["pos"]==pos)]
        for i in pool.head(n).index.tolist(): chosen.add(i)

    for pos in ["QB","RB","WR","TE"]: take(pos, need[pos])
    pool=df[(~df.index.isin(chosen))&(df["pos"].apply(flex_ok))]
    for i in pool.head(need["FLEX"]).index.tolist(): chosen.add(i)
    return df.loc[sorted(list(chosen))].copy(), df.loc[~df.index.isin(chosen)].copy()

def find_waivers(waiver_df, roster_df, top_n=10):
    if waiver_df.empty: return waiver_df
    w=waiver_df.copy()
    w["value"]=w.apply(lambda r: compute_value(r, LEAGUE_DEFAULTS), axis=1)
    w=w.sort_values(["value","pct_owned"], ascending=[False,True])
    have=set(roster_df["player"].astype(str).str.lower().tolist())
    w=w[~w["player"].astype(str).str.lower().isin(have)]
    return w.head(top_n)

def news_signals(df, limit=20):
    if df.empty: return df
    out=df.copy()
    if "time" in out.columns:
        try:
            out["time"]=pd.to_datetime(out["time"])
            out=out.sort_values("time", ascending=False)
        except Exception: pass
    cols=[c for c in ["time","player","team","tag","blurb","source"] if c in out.columns]
    return out[cols].head(limit)

def merge_roster_proj(roster, proj):
    if roster.empty: return proj
    return pd.merge(proj, roster[["player","pos","team","opp","status","bye"]].drop_duplicates(),
                    on=["player"], how="left", suffixes=("","_r"))

# --------- UI ----------
st.set_page_config(page_title="FFL Advisor", page_icon="🏈", layout="wide")
st.title("🏈 FFL Advisor — Lineup Optimizer & Waiver Finder")

with st.sidebar:
    st.header("Data Sources (optional)")
    roster_url = st.text_input("Roster CSV URL", os.getenv("ROSTER_CSV", DEFAULT_URLS["roster_csv"]))
    proj_url   = st.text_input("Projections CSV URL", os.getenv("PROJECTIONS_CSV", DEFAULT_URLS["projections_csv"]))
    waiver_url = st.text_input("Waiver CSV URL", os.getenv("WAIVER_CSV", DEFAULT_URLS["waiver_csv"]))
    def_url    = st.text_input("Defense vs Pos CSV URL", os.getenv("DEFENSE_CSV", DEFAULT_URLS["defense_csv"]))
    news_url   = st.text_input("News Signals CSV URL", os.getenv("NEWS_CSV", DEFAULT_URLS["news_csv"]))
    st.caption("Leave blank to use the built-in sample data.")
    st.markdown("---")
    st.header("League Settings")
    lg={}
    for k,v in LEAGUE_DEFAULTS.items():
        lg[k]=st.number_input(k, value=int(v), step=1) if isinstance(v,int) else st.number_input(k, value=float(v), step=0.5, format="%.2f")

# Load URLs or fall back to samples
raw_roster, raw_proj, raw_waiver, raw_def, raw_news = (
    fetch_csv(roster_url), fetch_csv(proj_url), fetch_csv(waiver_url), fetch_csv(def_url), fetch_csv(news_url)
)
if raw_roster.empty: raw_roster=SAMPLES["roster"]
if raw_proj.empty:   raw_proj=SAMPLES["projections"]
if raw_waiver.empty: raw_waiver=SAMPLES["waiver"]
if raw_def.empty:    raw_def=SAMPLES["defense"]
if raw_news.empty:   raw_news=SAMPLES["news"]

roster, proj, waiver, dvps, news = map(normalize_columns, [raw_roster, raw_proj, raw_waiver, raw_def]) + [raw_news.copy()]

# Merge DvP; guarantee def_rank exists
if not dvps.empty and "team" in proj.columns and "opp" in proj.columns and set(["pos","team","def_rank"]).issubset(dvps.columns):
    proj = pd.merge(proj, dvps[["pos","team","def_rank"]].rename(columns={"team":"opp"}), on=["pos","opp"], how="left")
proj["def_rank"] = proj.get("def_rank", pd.Series([16]*len(proj))).fillna(16)

roster_proj = merge_roster_proj(roster, proj) if not proj.empty else roster.copy()

tab1, tab2, tab3, tab4 = st.tabs(["Optimize Lineup","Waiver Targets","Cheat Sheet","News (Signals)"])

with tab1:
    st.subheader("Best Weekly Lineup (sample-ready)")
    starters, bench = fill_lineup(roster_proj, lg)
    if starters.empty:
        st.info("Add roster+projections CSVs or use the samples via blank URLs.")
    else:
        need={"QB":lg["qb_slots"],"RB":lg["rb_slots"],"WR":lg["wr_slots"],"TE":lg["te_slots"],"FLEX":lg["flex_slots"]}
        slots=[]
        for _,r in starters.sort_values("pos").iterrows():
            p=r["pos"]
            if p in need and need[p]>0: slots.append(p); need[p]-=1
            else: slots.append("FLEX")
        starters["slot"]=slots
        st.success("✅ Suggested Starters")
        st.dataframe(starters[["slot","player","pos","team","opp","proj","status","def_rank","value"]])
        st.warning("🧠 Bench (next-best)")
        st.dataframe(bench[["player","pos","team","opp","proj","status","def_rank","value"]].head(25))
        upgrades=[]
        for _,b in bench.iterrows():
            for i,s in starters.iterrows():
                ok=(s["slot"]==b["pos"]) or (s["slot"]=="FLEX" and b["pos"] in {"RB","WR","TE"})
                delta=float(b.get("value",0))-float(s.get("value",0))
                if ok and delta>0.6:
                    upgrades.append({"Swap In":f'{b["player"]} ({b["pos"]})',"Swap Out":f'{s["player"]} ({s["slot"]})',"Delta":round(delta,2)})
        if upgrades:
            st.info("🔁 Potential Upgrades (value delta > 0.6)")
            st.dataframe(pd.DataFrame(upgrades).sort_values("Delta", ascending=False).head(12))

with tab2:
    st.subheader("Top Waiver / Free Agents (sample-ready)")
    picks = find_waivers(waiver, roster, top_n=15)
    st.dataframe(picks[["player","pos","team","opp","proj","pct_owned","status","def_rank","value"]])

with tab3:
    st.subheader("Cheat Sheet (All Projections)")
    tmp=proj.copy(); tmp["value"]=tmp.apply(lambda r: compute_value(r,lg), axis=1)
    st.dataframe(tmp.sort_values("value", ascending=False)[["player","pos","team","opp","proj","status","def_rank","value"]].head(200))

with tab4:
    st.subheader("Signal-Only NFL News (sample-ready)")
    def _signals(df):
        if df.empty: return df
        out=df.copy()
        if "time" in out.columns:
            try: out["time"]=pd.to_datetime(out["time"]); out=out.sort_values("time", ascending=False)
            except Exception: pass
        cols=[c for c in ["time","player","team","tag","blurb","source"] if c in out.columns]
        return out[cols].head(20)
    st.dataframe(_signals(SAMPLES["news"]))
