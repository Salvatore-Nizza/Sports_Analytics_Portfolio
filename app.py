import streamlit as st
import pandas as pd
import os
import re
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from statsbombpy import sb
import soccerdata as sd
import warnings

# Ignore soccerdata warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Sports Analytics Hub", layout="wide", page_icon="⚽")

# ==========================================
# --- 1. DATA ENGINE (DUAL SAVE SYSTEM) ---
# ==========================================
@st.cache_resource
def connect_database():
    load_dotenv()
    target = os.getenv("DB_TARGET", "SQLITE")
    
    # 1. Always prepare the SQLite connection (Portable SSD)
    project_folder = os.path.dirname(os.path.abspath(__file__))
    clean_path = os.path.join(project_folder, "sports_analytics.db").replace("\\", "/")
    engine_sqlite = create_engine(f"sqlite:///{clean_path}")
    
    # 2. Database Routing
    if target == "POSTGRESQL":
        # Desktop Mode: Postgres is Primary, SQLite is Mirror
        db_password = os.getenv("DB_PASSWORD")
        engine_pg = create_engine(f"postgresql://postgres:{db_password}@localhost:5432/sports_analytics")
        return engine_pg, engine_sqlite 
    else:
        # Portable Mode: Only SQLite
        return engine_sqlite, None

engine_primary, engine_mirror = connect_database()

def save_data_to_db(df, table_name):
    """Saves data to Primary DB and Mirrors it to SQLite if available"""
    df.to_sql(table_name, engine_primary, if_exists='replace', index=False)
    
    if engine_mirror is not None:
        df.to_sql(table_name, engine_mirror, if_exists='replace', index=False)
        return f"✅ Sync Complete: Data saved to PostgreSQL & mirrored to SQLite ({table_name})"
    else:
        return f"✅ Offline Save: Data saved locally to SSD ({table_name})"

def format_db_name(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return re.sub(r'\s+', '_', text)

def format_visual_name(text):
    return str(text).replace("_", " ").title()

@st.cache_data
def get_competitions():
    return sb.competitions()

@st.cache_data
def get_matches(comp_id, season_id):
    return sb.matches(competition_id=comp_id, season_id=season_id)

# ==========================================
# --- SIDEBAR: MAIN NAVIGATION ---
# ==========================================
st.sidebar.title("⚙️ Main Navigation")

if engine_mirror is not None:
    st.sidebar.success("🟢 Desktop Mode: Sync Active")
else:
    st.sidebar.warning("🟡 Portable Mode: SSD Only")

app_mode = st.sidebar.radio(
    "Select Action:", 
    ["📂 Explore Database", "📥 Download New Data"]
)
st.sidebar.markdown("---")

# ==========================================
# MODE 1: DOWNLOAD NEW DATA
# ==========================================
if app_mode == "📥 Download New Data":
    st.title("📥 Data Download Center")
    
    provider = st.selectbox("🌐 Select Data Provider:", ["StatsBomb (Detailed Event Data)", "FBref (Aggregate Stats & Fixtures)"])
    st.markdown("---")
    
    # ----------------------------------
    # STATSBOMB FLOW
    # ----------------------------------
    if provider == "StatsBomb (Detailed Event Data)":
        st.subheader("StatsBomb Navigator")
        comps_df = get_competitions()
        
        col1, col2 = st.columns(2)
        with col1:
            comp_name = st.selectbox("🏆 Competition:", comps_df['competition_name'].unique().tolist())
            filtered_comp = comps_df[comps_df['competition_name'] == comp_name]
            comp_id = filtered_comp['competition_id'].iloc[0]
            
        with col2:
            season_name = st.selectbox("📅 Season:", filtered_comp['season_name'].unique().tolist())
            season_id = filtered_comp[filtered_comp['season_name'] == season_name]['season_id'].iloc[0]
            
        matches_df = get_matches(comp_id, season_id)
        
        if not matches_df.empty:
            st.markdown("### Download Mode")
            tab_single, tab_season = st.tabs(["⚽ Single Match", "🏆 Full Season Bulk"])
            
            with tab_single:
                matches_df['match_label'] = matches_df['match_date'] + " | " + matches_df['home_team'] + " vs " + matches_df['away_team']
                match_dict = dict(zip(matches_df['match_label'], matches_df['match_id']))
                selected_match = st.selectbox("Select Match:", list(match_dict.keys()))
                
                if st.button("🚀 Download Match", type="primary"):
                    match_id_sel = match_dict[selected_match]
                    with st.spinner('Extracting events...'):
                        events_df = sb.events(match_id=match_id_sel)
                        for c in events_df.columns:
                            if events_df[c].apply(type).eq(dict).any() or events_df[c].apply(type).eq(list).any():
                                events_df[c] = events_df[c].astype(str)
                        
                        table_name = f"statsbomb__{format_db_name(comp_name)}__{format_db_name(season_name)}__match_{match_id_sel}"
                        success_msg = save_data_to_db(events_df, table_name)
                    st.success(success_msg)
            
            with tab_season:
                st.info(f"You are about to download all {len(matches_df)} matches. This may take several minutes.")
                if st.button("⚡ Download FULL SEASON", type="primary"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    df_list = []
                    total_matches = len(matches_df)
                    
                    for i, row in matches_df.iterrows():
                        m_id = row['match_id']
                        status_text.text(f"Downloading match {i+1} of {total_matches}: {row['home_team']} vs {row['away_team']}...")
                        try:
                            df_ev = sb.events(match_id=m_id)
                            for c in df_ev.columns:
                                if df_ev[c].apply(type).eq(dict).any() or df_ev[c].apply(type).eq(list).any():
                                    df_ev[c] = df_ev[c].astype(str)
                            df_list.append(df_ev)
                        except:
                            pass
                        progress_bar.progress((i + 1) / total_matches)
                    
                    if df_list:
                        status_text.text("Merging and saving to database...")
                        full_season_df = pd.concat(df_list, ignore_index=True)
                        season_table_name = f"statsbomb__{format_db_name(comp_name)}__{format_db_name(season_name)}__full_season"
                        success_msg = save_data_to_db(full_season_df, season_table_name)
                        st.success(success_msg)
                        st.balloons()
    
    # ----------------------------------
    # FBREF FLOW
    # ----------------------------------
    elif provider == "FBref (Aggregate Stats & Fixtures)":
        st.subheader("FBref Navigator")
        fbref_leagues = {
            "Serie A": "ITA-Serie A", "Premier League": "ENG-Premier League", 
            "La Liga": "ESP-La Liga", "Bundesliga": "GER-Bundesliga", "Ligue 1": "FRA-Ligue 1"
        }
        
        col1, col2 = st.columns(2)
        with col1:
            league_choice = st.selectbox("🏆 League:", list(fbref_leagues.keys()))
        with col2:
            start_year = st.number_input("📅 Start Year (e.g., 2023 for 23/24):", min_value=2010, max_value=2025, value=2023)
            
        data_type = st.radio("What to download?", ["Team Stats", "Fixtures & Results"])
        
        if st.button("🚀 Download from FBref", type="primary"):
            season_fmt = f"{start_year}/{str(start_year+1)[-2:]}"
            league_code = fbref_leagues[league_choice]
            
            with st.spinner("Connecting to FBref..."):
                try:
                    fbref_api = sd.FBref(leagues=league_code, seasons=season_fmt)
                    if data_type == "Team Stats":
                        df = fbref_api.read_team_season_stats(stat_type="standard")
                        detail = "team_stats"
                    else:
                        df = fbref_api.read_schedule()
                        detail = "fixtures"
                        
                    df = df.reset_index()
                    df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else str(col) for col in df.columns]
                    table_name = f"fbref__{format_db_name(league_choice)}__{start_year}_{start_year+1}__{detail}"
                    success_msg = save_data_to_db(df, table_name)
                    st.success(success_msg)
                except Exception as e:
                    st.error(f"Error: {e}")

# ==========================================
# MODE 2: EXPLORE DATABASE
# ==========================================
elif app_mode == "📂 Explore Database":
    st.title("📁 Sports Database Explorer")
    
    # IMPORT THE MODULE FOR PHASE 1
    from moduli_analisi.fase1_giocatori import create_player_profile
    
    inspector = inspect(engine_primary)
    available_tables = inspector.get_table_names()
    db_tree = {}
    
    for tab in available_tables:
        if "__" in tab:
            parts = tab.split("__")
            if len(parts) >= 4:
                source = format_visual_name(parts[0])
                comp = format_visual_name(parts[1])
                season = format_visual_name(parts[2]).replace(" ", "/")
                detail = format_visual_name(parts[3])
                
                if source not in db_tree: db_tree[source] = {}
                if comp not in db_tree[source]: db_tree[source][comp] = {}
                if season not in db_tree[source][comp]: db_tree[source][comp][season] = {}
                db_tree[source][comp][season][detail] = tab

    if not db_tree:
        st.warning("No structured tables found. Go to 'Download New Data' to get started!")
    else:
        st.sidebar.subheader("Your Data")
        src_choice = st.sidebar.selectbox("📂 Source", list(db_tree.keys()))
        comp_choice = st.sidebar.selectbox("🏆 Competition", list(db_tree[src_choice].keys()))
        season_choice = st.sidebar.selectbox("📅 Season", list(db_tree[src_choice][comp_choice].keys()))
        detail_choice = st.sidebar.selectbox("📊 Data Detail", list(db_tree[src_choice][comp_choice][season_choice].keys()))
        
        final_table_name = db_tree[src_choice][comp_choice][season_choice][detail_choice]

        tab_raw, tab_player, tab_team = st.tabs(["📊 Raw Data", "👤 Player Profile", "🏟️ Team Analysis"])
        
        # Load Data once to use across tabs
        query = f"SELECT * FROM {final_table_name}"
        df = pd.read_sql(query, engine_primary)
        
        with tab_raw:
            st.caption(f"SQL Table: `{final_table_name}`")
            st.write(f"Total Records: **{len(df)}**")
            st.dataframe(df, width="stretch")
            
        with tab_player:
            # We call our English translated Phase 1 module
            create_player_profile(df, src_choice)
            
        with tab_team:
            st.info("Awaiting Phase 2 (Team Analysis & Heatmaps).")