import streamlit as st
import pandas as pd
import os
import re
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from statsbombpy import sb
import soccerdata as sd
import warnings

# Nascondiamo i warning di soccerdata
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Hub Analisi Sportiva", layout="wide", page_icon="⚽")

# --- 1. FUNZIONI DI BASE E CONNESSIONE INTELLIGENTE ---
@st.cache_resource
def connetti_db():
    load_dotenv()
    target_database = os.getenv("DB_TARGET", "SQLITE")
    
    if target_database == "POSTGRESQL":
        # Configurazione per il PC Fisso
        db_password = os.getenv("DB_PASSWORD")
        db_url = f"postgresql://postgres:{db_password}@localhost:5432/sports_analytics"
    else:
        # --- TRUCCO PER L'HARD DISK ESTERNO ---
        # Trova il percorso assoluto della cartella in cui si trova questo file app.py
        cartella_progetto = os.path.dirname(os.path.abspath(__file__))
        
        # Unisce la cartella al nome del file del database
        percorso_completo_db = os.path.join(cartella_progetto, "sports_analytics.db")
        
        # Sostituisce i backslash di Windows (\) con gli slash (/) richiesti da SQLite
        percorso_pulito = percorso_completo_db.replace("\\", "/")
        
        db_url = f"sqlite:///{percorso_pulito}"
        
    return create_engine(db_url)

def formatta_nome_db(testo):
    """Pulisce i nomi per SQL: minuscolo e spazi sostituiti da underscore"""
    testo = str(testo).lower()
    testo = re.sub(r'[^a-z0-9\s]', '', testo)
    return re.sub(r'\s+', '_', testo)

def formatta_nome_visuale(testo):
    """Fa il contrario: trasforma 'champions_league' in 'Champions League' per i menu"""
    return str(testo).replace("_", " ").title()

engine = connetti_db()

@st.cache_data
def ottieni_competizioni():
    return sb.competitions()

@st.cache_data
def ottieni_partite(comp_id, season_id):
    return sb.matches(competition_id=comp_id, season_id=season_id)

# ==========================================
# --- BARRA LATERALE: NAVIGAZIONE ---
# ==========================================
st.sidebar.title("⚙️ Navigazione Principale")
modalita = st.sidebar.radio(
    "Cosa vuoi fare?", 
    ["📂 Esplora Database", "📥 Scarica Nuovi Dati"]
)
st.sidebar.markdown("---")

# ==========================================
# MODALITÀ 1: SCARICA NUOVI DATI
# ==========================================
if modalita == "📥 Scarica Nuovi Dati":
    st.title("📥 Centro Download Dati")
    
    # SCELTA DEL DATABASE
    fornitore = st.selectbox("🌐 Scegli il Fornitore Dati:", ["StatsBomb (Dati Evento Dettagliati)", "FBref (Statistiche Aggregate e Calendari)"])
    st.markdown("---")
    
    # ----------------------------------
    # FLUSSO STATSBOMB
    # ----------------------------------
    if fornitore == "StatsBomb (Dati Evento Dettagliati)":
        st.subheader("Navigatore StatsBomb")
        comps_df = ottieni_competizioni()
        
        col1, col2 = st.columns(2)
        with col1:
            scelta_comp_nome = st.selectbox("🏆 Competizione:", comps_df['competition_name'].unique().tolist())
            comp_filtrata = comps_df[comps_df['competition_name'] == scelta_comp_nome]
            comp_id = comp_filtrata['competition_id'].iloc[0]
            
        with col2:
            scelta_stag_nome = st.selectbox("📅 Stagione:", comp_filtrata['season_name'].unique().tolist())
            season_id = comp_filtrata[comp_filtrata['season_name'] == scelta_stag_nome]['season_id'].iloc[0]
            
        partite_df = ottieni_partite(comp_id, season_id)
        
        if not partite_df.empty:
            st.markdown("### Modalità di Download")
            tab_singola, tab_stagione = st.tabs(["⚽ Scarica Singola Partita", "🏆 Scarica INTERA Stagione"])
            
            # TAB 1: SINGOLA PARTITA
            with tab_singola:
                partite_df['match_label'] = partite_df['match_date'] + " | " + partite_df['home_team'] + " vs " + partite_df['away_team']
                diz_partite = dict(zip(partite_df['match_label'], partite_df['match_id']))
                scelta_partita = st.selectbox("Scegli la Partita:", list(diz_partite.keys()))
                
                if st.button("🚀 Scarica Partita", type="primary"):
                    match_id_sel = diz_partite[scelta_partita]
                    with st.spinner('Estrazione in corso...'):
                        df_eventi = sb.events(match_id=match_id_sel)
                        # Pulizia colonne complesse
                        for c in df_eventi.columns:
                            if df_eventi[c].apply(type).eq(dict).any() or df_eventi[c].apply(type).eq(list).any():
                                df_eventi[c] = df_eventi[c].astype(str)
                        
                        nome_tab = f"statsbomb__{formatta_nome_db(scelta_comp_nome)}__{formatta_nome_db(scelta_stag_nome)}__partita_{match_id_sel}"
                        df_eventi.to_sql(nome_tab, engine, if_exists='replace', index=False)
                    st.success(f"Partita salvata: {nome_tab}")
            
            # TAB 2: INTERA STAGIONE (BULK DOWNLOAD)
            with tab_stagione:
                st.info(f"Stai per scaricare tutte le {len(partite_df)} partite della stagione. Potrebbe volerci qualche minuto.")
                if st.button("⚡ Scarica TUTTA LA STAGIONE (Lungo)", type="primary"):
                    progress_bar = st.progress(0)
                    testo_stato = st.empty()
                    
                    lista_dataframe = []
                    totale = len(partite_df)
                    
                    for i, riga in partite_df.iterrows():
                        m_id = riga['match_id']
                        testo_stato.text(f"Scaricamento partita {i+1} di {totale}: {riga['home_team']} vs {riga['away_team']}...")
                        try:
                            df_ev = sb.events(match_id=m_id)
                            # Pulizia colonne
                            for c in df_ev.columns:
                                if df_ev[c].apply(type).eq(dict).any() or df_ev[c].apply(type).eq(list).any():
                                    df_ev[c] = df_ev[c].astype(str)
                            lista_dataframe.append(df_ev)
                        except:
                            pass # Salta se c'è un errore su una singola partita
                        
                        progress_bar.progress((i + 1) / totale)
                    
                    if lista_dataframe:
                        testo_stato.text("Unione dei dati e salvataggio nel database...")
                        df_completo = pd.concat(lista_dataframe, ignore_index=True)
                        nome_tab_stagione = f"statsbomb__{formatta_nome_db(scelta_comp_nome)}__{formatta_nome_db(scelta_stag_nome)}__stagione_completa"
                        df_completo.to_sql(nome_tab_stagione, engine, if_exists='replace', index=False)
                        st.success(f"✅ Download stagionale completato! Salvate {len(df_completo)} righe in: {nome_tab_stagione}")
                        st.balloons()
    
    # ----------------------------------
    # FLUSSO FBREF
    # ----------------------------------
    elif fornitore == "FBref (Statistiche Aggregate e Calendari)":
        st.subheader("Navigatore FBref")
        camp_fbref = {
            "Serie A": "ITA-Serie A", "Premier League": "ENG-Premier League", 
            "La Liga": "ESP-La Liga", "Bundesliga": "GER-Bundesliga", "Ligue 1": "FRA-Ligue 1"
        }
        
        col1, col2 = st.columns(2)
        with col1:
            scelta_lega = st.selectbox("🏆 Campionato:", list(camp_fbref.keys()))
        with col2:
            anno = st.number_input("📅 Anno di inizio (es. 2023 per 23/24):", min_value=2010, max_value=2025, value=2023)
            
        tipo_dato = st.radio("Cosa vuoi scaricare?", ["Statistiche Squadre", "Calendario e Risultati"])
        
        if st.button("🚀 Scarica da FBref", type="primary"):
            stagione_fmt = f"{anno}/{str(anno+1)[-2:]}"
            lega_code = camp_fbref[scelta_lega]
            
            with st.spinner("Connessione a FBref in corso..."):
                try:
                    fbref_api = sd.FBref(leagues=lega_code, seasons=stagione_fmt)
                    if tipo_dato == "Statistiche Squadre":
                        df = fbref_api.read_team_season_stats(stat_type="standard")
                        dettaglio = "statistiche_squadre"
                    else:
                        df = fbref_api.read_schedule()
                        dettaglio = "calendario"
                        
                    # Pulizia colonne
                    df = df.reset_index()
                    df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else str(col) for col in df.columns]
                    
                    nome_tab = f"fbref__{formatta_nome_db(scelta_lega)}__{anno}_{anno+1}__{dettaglio}"
                    df.to_sql(nome_tab, engine, if_exists='replace', index=False)
                    st.success(f"✅ Dati FBref salvati in: {nome_tab}")
                except Exception as e:
                    st.error(f"Errore: {e}")

# ==========================================
# MODALITÀ 2: ESPLORA DATABASE
# ==========================================
elif modalita == "📂 Esplora Database":
    st.title("📁 Esploratore Database Sportivo")
    
    inspector = inspect(engine)
    tabelle_disponibili = inspector.get_table_names()
    
    albero_db = {}
    
    for tab in tabelle_disponibili:
        if "__" in tab:
            parti = tab.split("__")
            if len(parti) >= 4:
                # Applichiamo la formattazione visiva "bella" (da statsbomb a Statsbomb, ecc.)
                fonte = formatta_nome_visuale(parti[0])
                comp = formatta_nome_visuale(parti[1])
                stag = formatta_nome_visuale(parti[2]).replace(" ", "/") # Per mostrare 2023/2024
                dettaglio = formatta_nome_visuale(parti[3])
                
                if fonte not in albero_db: albero_db[fonte] = {}
                if comp not in albero_db[fonte]: albero_db[fonte][comp] = {}
                if stag not in albero_db[fonte][comp]: albero_db[fonte][comp][stag] = {}
                albero_db[fonte][comp][stag][dettaglio] = tab

    if not albero_db:
        st.warning("Nessuna tabella strutturata trovata. (Ricorda di cancellare le vecchie tabelle da DBeaver!)")
    else:
        st.sidebar.subheader("I tuoi Dati")
        
        # MENU A CASCATA (Visivamente pulito)
        scelta_fonte = st.sidebar.selectbox("📂 Fonte Dati", list(albero_db.keys()))
        scelta_comp = st.sidebar.selectbox("🏆 Competizione", list(albero_db[scelta_fonte].keys()))
        scelta_stag = st.sidebar.selectbox("📅 Stagione", list(albero_db[scelta_fonte][scelta_comp].keys()))
        scelta_dettaglio = st.sidebar.selectbox("📊 Dettaglio Dati", list(albero_db[scelta_fonte][scelta_comp][scelta_stag].keys()))
        
        tabella_selezionata_finale = albero_db[scelta_fonte][scelta_comp][scelta_stag][scelta_dettaglio]

        tab_raw, tab_giocatori, tab_squadra = st.tabs(["📊 Dati Grezzi", "👤 Scheda Atleta", "🏟️ Analisi Squadra"])
        
        with tab_raw:
            st.caption(f"Tabella tecnica nel DB: `{tabella_selezionata_finale}`")
            query = f"SELECT * FROM {tabella_selezionata_finale}"
            df = pd.read_sql(query, engine)
            st.write(f"Record totali: **{len(df)}**")
            st.dataframe(df, width="stretch")
            
        with tab_giocatori:
            st.info("In attesa della Fase 1")
        with tab_squadra:
            st.info("In attesa della Fase 2")