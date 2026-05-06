import streamlit as st
import pandas as pd

   # Titolo dell'app
st.title("⚽ La mia Piattaforma di Sports Analytics")

   # Creiamo un finto dataset per prova
dati = pd.DataFrame({
       'Giocatore': ['Messi', 'Ronaldo', 'Mbappe'],
       'Gol': [20, 18, 25]
   })

   # Mostriamo la tabella
st.write("Dati di prova:")
st.dataframe(dati)