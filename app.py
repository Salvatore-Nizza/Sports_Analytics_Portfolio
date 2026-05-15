import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect

st.set_page_config(page_title="Hub Analisi Sportiva", layout="wide")

# CONNESSIONE AL DATABASE
@st.cache_resource
def connetti_db():
    load_dotenv()
    db_password = os.getenv("DB_PASSWORD")
    db_url = f"postgresql://postgres:{db_password}@localhost:5432/sports_analytics"
    return create_engine(db_url)

engine = connetti_db()

# ESPLORAZIONE DINAMICA DATABASE
inspector = inspect(engine)
tabelle_disponibili = inspector.get_table_names()

st.title("⚙️ HUB Analisi Sportiva - Esplorazione Dati")
st.markdown("Seleziona una fonte dati dalla barra laterale per analizzare.")

# INTERFACCIA LATERALE
st.sidebar.header("Data Selector")

if not tabelle_disponibili:
    st.warning("Il database è vuoto. Usa il tuo master_script.py per scaricare dei dati!")
else:
    # Menu a tendina auto-popolante
    tabella_selezionata = st.sidebar.selectbox("Scegli la tabella dal Database:", tabelle_disponibili)
    
    # Struttura a Tab per le future implementazioni
    tab_raw, tab_giocatori, tab_squadra = st.tabs(["📊 Dati Grezzi", "👤 Scheda Atleta", "🏟️ Analisi Squadra"])
    
    with tab_raw:
        st.subheader(f"Vista Tabella: {tabella_selezionata}")
        
        # Carica il dataframe e lo mostra
        query = f"SELECT * FROM {tabella_selezionata}"
        df = pd.read_sql(query, engine)
        
        st.write(f"Questa tabella contiene **{len(df)}** record.")
        st.dataframe(df, width="stretch")
    
    with tab_giocatori:
        st.info("Qui costruiremo la scheda stile videogioco con i Radar Chart. (In attesa della Fase 1)")
        
    with tab_squadra:
        st.info("Qui inseriremo le mappe del campo e i confronti tra squadre. (In attesa della Fase 2)")