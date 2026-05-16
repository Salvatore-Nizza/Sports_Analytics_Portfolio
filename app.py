import streamlit as st
import pandas as pd
import os
import re
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from statsbombpy import sb

st.set_page_config(page_title="Hub Analisi Sportiva", layout="wide", page_icon="⚽")

# --- 1. FUNZIONI DI BASE E DATABASE ---
@st.cache_resource
def connetti_db():
    load_dotenv()
    db_password = os.getenv("DB_PASSWORD")
    db_url = f"postgresql://postgres:{db_password}@localhost:5432/sports_analytics"
    return create_engine(db_url)

def formatta_nome_db(testo):
    """Pulisce i nomi per renderli compatibili con PostgreSQL"""
    testo = str(testo).lower()
    testo = re.sub(r'[^a-z0-9\s]', '', testo)
    return re.sub(r'\s+', '_', testo)

engine = connetti_db()

# --- 2. FUNZIONI CACHE PER STATSBOMB (Per non rallentare l'app) ---
@st.cache_data
def ottieni_competizioni():
    return sb.competitions()

@st.cache_data
def ottieni_partite(comp_id, season_id):
    return sb.matches(competition_id=comp_id, season_id=season_id)

# ==========================================
# --- STRUTTURA DELLA BARRA LATERALE ---
# ==========================================
st.sidebar.title("⚙️ Navigazione Principale")
modalita = st.sidebar.radio(
    "Cosa vuoi fare?", 
    ["📂 Esplora Database (Dati Salvati)", "📥 Scarica Nuovi Dati (StatsBomb)"]
)
st.sidebar.markdown("---")

# ==========================================
# MODALITÀ 1: SCARICA NUOVI DATI
# ==========================================
if modalita == "📥 Scarica Nuovi Dati (StatsBomb)":
    st.title("📥 Navigatore StatsBomb API")
    st.markdown("Cerca e scarica nuove partite direttamente dai server di StatsBomb nel tuo database PostgreSQL.")
    
    try:
        # Recupera tutte le competizioni
        comps_df = ottieni_competizioni()
        
        # 1. Menu Competizione
        lista_competizioni = comps_df['competition_name'].unique().tolist()
        scelta_comp_nome = st.selectbox("🏆 1. Scegli la Competizione:", lista_competizioni)
        
        # Filtra i dati in base alla competizione scelta
        comp_filtrata = comps_df[comps_df['competition_name'] == scelta_comp_nome]
        comp_id = comp_filtrata['competition_id'].iloc[0]
        
        # 2. Menu Stagione
        lista_stagioni = comp_filtrata['season_name'].unique().tolist()
        scelta_stag_nome = st.selectbox("📅 2. Scegli la Stagione:", lista_stagioni)
        
        season_id = comp_filtrata[comp_filtrata['season_name'] == scelta_stag_nome]['season_id'].iloc[0]
        
        # 3. Menu Partita
        partite_df = ottieni_partite(comp_id, season_id)
        
        if partite_df.empty:
            st.warning("Nessuna partita trovata per questa stagione.")
        else:
            # Creiamo un'etichetta leggibile per il menu a tendina (Squadra A vs Squadra B)
            partite_df['match_label'] = partite_df['match_date'] + " | " + partite_df['home_team'] + " vs " + partite_df['away_team']
            
            # Creiamo un dizionario per legare l'etichetta bella all'ID della partita
            dizionario_partite = dict(zip(partite_df['match_label'], partite_df['match_id']))
            
            scelta_partita_label = st.selectbox("⚽ 3. Scegli la Partita:", list(dizionario_partite.keys()))
            match_id_selezionato = dizionario_partite[scelta_partita_label]
            
            st.info(f"ID Partita Selezionata: {match_id_selezionato}")
            
            # 4. BOTTONE DI DOWNLOAD
            if st.button("🚀 Scarica e Salva nel Database", type="primary"):
                with st.spinner('Estrazione dei dati evento in corso. Potrebbe volerci un minuto...'):
                    # Estrae i dati
                    eventi_df = sb.events(match_id=match_id_selezionato)
                    
                    # Pulisce i dati per SQL
                    for colonna in eventi_df.columns:
                        if eventi_df[colonna].apply(type).eq(dict).any() or eventi_df[colonna].apply(type).eq(list).any():
                            eventi_df[colonna] = eventi_df[colonna].astype(str)
                    
                    # Genera il nome tabella
                    nome_pulito_comp = formatta_nome_db(scelta_comp_nome)
                    nome_pulito_stag = formatta_nome_db(scelta_stag_nome)
                    nome_tabella = f"statsbomb__{nome_pulito_comp}__{nome_pulito_stag}__match_{match_id_selezionato}"
                    
                    # Salva nel DB
                    eventi_df.to_sql(nome_tabella, engine, if_exists='replace', index=False)
                    
                st.success(f"✅ Fatto! {len(eventi_df)} eventi salvati con successo nella tabella: {nome_tabella}")
                st.balloons() # Una piccola animazione di festa di Streamlit!

    except Exception as e:
        st.error(f"Si è verificato un errore di connessione API: {e}")

# ==========================================
# MODALITÀ 2: ESPLORA DATABASE (Il codice di prima)
# ==========================================
elif modalita == "📂 Esplora Database (Dati Salvati)":
    st.title("📁 Esploratore Database Sportivo")
    st.markdown("Analizza i dati che hai già scaricato nel tuo database.")
    
    inspector = inspect(engine)
    tabelle_disponibili = inspector.get_table_names()
    
    albero_db = {}
    tabelle_vecchie = []
    
    for tab in tabelle_disponibili:
        if "__" in tab:
            parti = tab.split("__")
            if len(parti) >= 4:
                fonte, comp, stag, dettaglio = parti[0].capitalize(), parti[1].replace("_", " ").title(), parti[2].replace("_", "/").title(), parti[3].replace("_", " ").title()
                if fonte not in albero_db: albero_db[fonte] = {}
                if comp not in albero_db[fonte]: albero_db[fonte][comp] = {}
                if stag not in albero_db[fonte][comp]: albero_db[fonte][comp][stag] = {}
                albero_db[fonte][comp][stag][dettaglio] = tab
        else:
            tabelle_vecchie.append(tab)
            
    tabella_selezionata_finale = None
    
    if not tabelle_disponibili:
        st.warning("Il database è vuoto. Vai nella sezione 'Scarica Nuovi Dati' per iniziare!")
    else:
        st.sidebar.subheader("I tuoi Dati")
        fonti_disponibili = list(albero_db.keys())
        if tabelle_vecchie: fonti_disponibili.append("Vecchi Salvataggi ⚠️")
        
        scelta_fonte = st.sidebar.selectbox("📂 Fonte Dati", fonti_disponibili)
        
        if scelta_fonte == "Vecchi Salvataggi ⚠️":
            tabella_selezionata_finale = st.sidebar.selectbox("📄 Seleziona Tabella", tabelle_vecchie)
        else:
            comp_disponibili = list(albero_db[scelta_fonte].keys())
            scelta_comp = st.sidebar.selectbox("🏆 Competizione", comp_disponibili)
            
            stag_disponibili = list(albero_db[scelta_fonte][scelta_comp].keys())
            scelta_stag = st.sidebar.selectbox("📅 Stagione", stag_disponibili)
            
            dettagli_disponibili = list(albero_db[scelta_fonte][scelta_comp][scelta_stag].keys())
            scelta_dettaglio = st.sidebar.selectbox("📊 Dettaglio Dati", dettagli_disponibili)
            
            tabella_selezionata_finale = albero_db[scelta_fonte][scelta_comp][scelta_stag][scelta_dettaglio]

    if tabella_selezionata_finale:
        tab_raw, tab_giocatori, tab_squadra = st.tabs(["📊 Dati Grezzi", "👤 Scheda Atleta", "🏟️ Analisi Squadra"])
        
        with tab_raw:
            st.caption(f"Nome tabella SQL: {tabella_selezionata_finale}")
            query = f"SELECT * FROM {tabella_selezionata_finale}"
            df = pd.read_sql(query, engine)
            st.write(f"Righe: **{len(df)}**")
            st.dataframe(df, width="stretch")
        
        with tab_giocatori:
            st.info("In attesa della Fase 1")
        with tab_squadra:
            st.info("In attesa della Fase 2")