import streamlit as st
import pandas as pd
import plotly.express as px

def crea_scheda_atleta(df):
    st.subheader("👤 Analisi Profilo Atleta")
    
    # 1. CONTROLLO COMPATIBILITÀ DATI
    # Verifichiamo che la tabella caricata sia un database di eventi (es. StatsBomb)
    if 'player' not in df.columns or 'type' not in df.columns:
        st.warning("⚠️ I dati selezionati non contengono il dettaglio dei singoli giocatori o degli eventi. Scegli una tabella 'partita' o 'stagione_completa' di StatsBomb.")
        return

    # 2. SELEZIONE GIOCATORE
    # Rimuoviamo i valori nulli (es. fischi dell'arbitro senza giocatore associato) e ordiniamo alfabeticamente
    giocatori_disponibili = sorted(df['player'].dropna().unique())
    scelta_giocatore = st.selectbox("🔍 Cerca e seleziona un atleta:", giocatori_disponibili)
    
    st.markdown("---")
    
    # Filtriamo il dataframe solo per il giocatore selezionato
    df_giocatore = df[df['player'] == scelta_giocatore]
    
    # 3. CALCOLO METRICHE BASE
    tot_eventi = len(df_giocatore)
    passaggi = len(df_giocatore[df_giocatore['type'] == 'Pass'])
    tiri = len(df_giocatore[df_giocatore['type'] == 'Shot'])
    dribbling = len(df_giocatore[df_giocatore['type'] == 'Dribble'])
    
    # Mostriamo le metriche in stile cruscotto
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("⚽ Azioni Totali", tot_eventi)
    col2.metric("👟 Passaggi", passaggi)
    col3.metric("🎯 Tiri", tiri)
    col4.metric("🏃‍♂️ Dribbling", dribbling)
    
    st.markdown("---")
    
    # 4. RADAR CHART (GRAFICO A RAGNATELA)
    st.markdown("#### 🕸️ Radar Chart - Stile di Gioco")
    
    # Prepariamo un dizionario con i dati da graficare
    # Nota: Stiamo calcolando i volumi assoluti per mostrare la struttura
    dati_radar = pd.DataFrame(dict(
        valore=[passaggi, tiri, dribbling, len(df_giocatore[df_giocatore['type'] == 'Interception']), len(df_giocatore[df_giocatore['type'] == 'Foul Committed'])],
        metrica=['Passaggi', 'Tiri', 'Dribbling', 'Intercetti', 'Falli Fatti']
    ))
    
    # Generiamo il grafico polare
    fig = px.line_polar(dati_radar, r='valore', theta='metrica', line_close=True, markers=True)
    fig.update_traces(fill='toself', line_color='#E03A3E') # Colore rosso sportivo
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, showticklabels=True)),
        margin=dict(l=40, r=40, t=20, b=20)
    )
    
    # Mostriamo il grafico in Streamlit
    st.plotly_chart(fig, use_container_width=True)