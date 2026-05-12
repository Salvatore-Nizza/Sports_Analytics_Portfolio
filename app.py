import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
import plotly.express as px  # NUOVA LIBRERIA PER GRAFICI AVANZATI

st.set_page_config(page_title="Sports Analytics Dashboard", layout="wide")

load_dotenv()
db_password = os.getenv("DB_PASSWORD")
db_url = f"postgresql://postgres:{db_password}@localhost:5432/sports_analytics"

@st.cache_resource
def get_engine():
    return create_engine(db_url)

engine = get_engine()

st.title("⚽ Analisi Finale Mondiali 2022")
st.markdown("Dati estratti direttamente da PostgreSQL")

analisi_selezionata = st.sidebar.radio(
    "Cosa vuoi analizzare?",
    ["Panoramica Match", "Performance Giocatori", "Analisi Tiri"]
)

if analisi_selezionata == "Panoramica Match":
    st.subheader("Statistiche Generali")
    query_totale = "SELECT type, COUNT(*) as totale FROM statsbomb_eventi_mondiale GROUP BY type ORDER BY totale DESC"
    df_totale = pd.read_sql(query_totale, engine)
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("Distribuzione Tipologia Eventi")
        st.dataframe(df_totale, width="stretch")
    with col2:
        passaggi = df_totale[df_totale['type'] == 'Pass']['totale'].values[0]
        st.metric("Passaggi Totali", passaggi)
        tiri = df_totale[df_totale['type'] == 'Shot']['totale'].values[0]
        st.metric("Tiri Totali", tiri)

elif analisi_selezionata == "Performance Giocatori":
    st.subheader("Top 10 Giocatori per Passaggi")
    
    query_pass = """
    SELECT player, team, COUNT(*) as numero_passaggi 
    FROM statsbomb_eventi_mondiale 
    WHERE type = 'Pass' 
    GROUP BY player, team 
    ORDER BY numero_passaggi DESC 
    LIMIT 10
    """
    df_pass = pd.read_sql(query_pass, engine)
    
    # --- NUOVA INTERATTIVITÀ: Ordinamento ---
    ordine = st.radio("Scegli l'ordinamento del grafico:", ["Dal maggiore al minore", "Alfabetico per Giocatore"])
    
    if ordine == "Dal maggiore al minore":
        df_pass = df_pass.sort_values(by="numero_passaggi", ascending=False)
    else:
        df_pass = df_pass.sort_values(by="player", ascending=True)

    # --- NUOVO GRAFICO PLOTLY ---
    fig = px.bar(df_pass, x='player', y='numero_passaggi', color='team', 
                 title="Passaggi Completati", text='numero_passaggi')
    st.plotly_chart(fig, width="stretch")
    
    st.dataframe(df_pass, width="stretch")

elif analisi_selezionata == "Analisi Tiri":
    st.subheader("Dettaglio Tiri: Messi vs Mbappé")
    
    query_tiri = """
    SELECT player, minute, shot_statsbomb_xg, shot_outcome 
    FROM statsbomb_eventi_mondiale 
    WHERE player IN ('Lionel Andrés Messi Cuccittini', 'Kylian Mbappé Lottin') 
      AND type = 'Shot'
    """
    df_tiri = pd.read_sql(query_tiri, engine)
    
    # --- NUOVA INTERATTIVITÀ: Filtri Dinamici ---
    col_filtro1, col_filtro2 = st.columns(2)
    
    with col_filtro1:
        # Crea un menu a tendina prendendo i nomi unici dal dataframe
        lista_giocatori = ["Tutti"] + list(df_tiri['player'].unique())
        scelta_giocatore = st.selectbox("Filtra per Giocatore:", lista_giocatori)
        
    with col_filtro2:
        lista_esiti = ["Tutti"] + list(df_tiri['shot_outcome'].unique())
        scelta_esito = st.selectbox("Filtra per Esito del Tiro:", lista_esiti)
        
    # Applichiamo i filtri scelti dall'utente al dataframe
    df_filtrato = df_tiri.copy()
    if scelta_giocatore != "Tutti":
        df_filtrato = df_filtrato[df_filtrato['player'] == scelta_giocatore]
        
    if scelta_esito != "Tutti":
        df_filtrato = df_filtrato[df_filtrato['shot_outcome'] == scelta_esito]
        
    # Mostriamo la tabella filtrata
    st.dataframe(df_filtrato,  width="stretch")