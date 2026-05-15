import pandas as pd
from statsbombpy import sb
import soccerdata as sd
import warnings
import sys
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

warnings.filterwarnings('ignore')

def salva_su_database(df, nome_tabella):
    print(f"\nTentativo di connessione al database per la tabella '{nome_tabella}'...")
    try:
        load_dotenv()
        password_segreta = os.getenv("DB_PASSWORD")
        stringa_connessione = f'postgresql://postgres:{password_segreta}@localhost:5432/sports_analytics'
        engine = create_engine(stringa_connessione)
        
        df.to_sql(nome_tabella, engine, if_exists='replace', index=False)
        print(f"✅ SUCCESSO! {len(df)} righe salvate in PostgreSQL nella tabella '{nome_tabella}'.")
    except Exception as e:
        print(f"❌ Errore durante il salvataggio: {e}")

def esploratore_statsbomb():
    print("\n" + "-"*40)
    print(" 🌍 NAVIGATORE STATSBOMB (Dati Evento) 🌍")
    print("-"*40)
    try:
        comps = sb.competitions()
        comps_view = comps[['competition_id', 'competition_name', 'competition_gender']].drop_duplicates()
        print("\n--- COMPETIZIONI ---")
        print(comps_view.to_string(index=False))
        comp_id = int(input("\n👉 Inserisci il 'competition_id': "))

        stagioni = comps[comps['competition_id'] == comp_id][['season_id', 'season_name']]
        print("\n--- STAGIONI ---")
        print(stagioni.to_string(index=False))
        season_id = int(input("\n👉 Inserisci il 'season_id': "))

        partite = sb.matches(competition_id=comp_id, season_id=season_id)
        partite_view = partite[['match_id', 'match_date', 'home_team', 'away_team', 'home_score', 'away_score']]
        print("\n--- PARTITE ---")
        print(partite_view.to_string(index=False))
        match_id = int(input("\n👉 Inserisci il 'match_id' della partita: "))

        print(f"\n⏳ Estrazione eventi per il match {match_id} in corso...")
        eventi = sb.events(match_id=match_id)
        
        for colonna in eventi.columns:
            if eventi[colonna].apply(type).eq(dict).any() or eventi[colonna].apply(type).eq(list).any():
                eventi[colonna] = eventi[colonna].astype(str)
                
        nome_tabella = f"statsbomb_match_{match_id}"
        salva_su_database(eventi, nome_tabella)
    except Exception as e:
        print(f"Errore: {e}")

def esploratore_fbref():
    print("\n" + "-"*40)
    print(" 📊 NAVIGATORE FBREF (Statistiche e Campionati) 📊")
    print("-"*40)
    
    campionati = {
        "1": "ITA-Serie A",
        "2": "ENG-Premier League",
        "3": "ESP-La Liga",
        "4": "GER-Bundesliga",
        "5": "FRA-Ligue 1"
    }
    
    print(" Scegli il campionato:")
    for key, value in campionati.items():
        print(f" {key}. {value}")
        
    scelta_camp = input("\n👉 Inserisci il numero del campionato: ")
    league = campionati.get(scelta_camp)
    
    if not league:
        print("Scelta non valida. Ritorno al menu.")
        return

    anno = input("👉 Inserisci l'anno di inizio stagione (es. 2022 per 2022/2023): ")
    stagione_formattata = f"{anno}/{str(int(anno)+1)[-2:]}"
    
    print("\n Cosa vuoi estrarre da FBref?")
    print(" 1. Statistiche aggregate delle squadre (Stagione intera)")
    print(" 2. Calendario e Risultati di tutte le partite")
    scelta_dati = input("👉 Inserisci il numero: ")
    
    try:
        fbref = sd.FBref(leagues=league, seasons=stagione_formattata)
        
        if scelta_dati == "1":
            print(f"\n⏳ Estrazione statistiche squadre {league} {stagione_formattata} in corso...")
            df = fbref.read_team_season_stats(stat_type="standard")
            nome_tabella = f"fbref_stats_{league.replace('-', '_').replace(' ', '').lower()}_{anno}"
        elif scelta_dati == "2":
            print(f"\n⏳ Estrazione calendario {league} {stagione_formattata} in corso...")
            df = fbref.read_schedule()
            nome_tabella = f"fbref_partite_{league.replace('-', '_').replace(' ', '').lower()}_{anno}"
        else:
            print("Scelta non valida.")
            return
            
        # Pulizia base per il database
        df = df.reset_index()
        df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else str(col) for col in df.columns]
        
        salva_su_database(df, nome_tabella)
    except Exception as e:
        print(f"Errore: {e}")

def menu_principale():
    while True:
        print("\n" + "="*50)
        print(" 🏆 SPORTS ANALYTICS MASTER HUB 🏆")
        print("="*50)
        print(" Scegli il database da interrogare:")
        print(" 1. ⚽ Calcio: StatsBomb (Dati Evento Singola Partita)")
        print(" 2. ⚽ Calcio: FBref (Statistiche Stagionali e Calendari)")
        print(" 3. 🏀 Basket: NBA API (In lavorazione 🚧)")
        print(" 4. 🏎️ Motori: FastF1 (In lavorazione 🚧)")
        print(" 5. 🏈 Football: NFL Play-by-Play (In lavorazione 🚧)")
        print(" 6. ⚾ Baseball: MLB Statcast (In lavorazione 🚧)")
        print(" 7. 🎾 Tennis: ATP/WTA Storico (In lavorazione 🚧)")
        print(" 0. ❌ Esci")
        print("="*50)

        scelta = input("Inserisci il numero e premi Invio: ")

        if scelta == "1":
            esploratore_statsbomb()
        elif scelta == "2":
            esploratore_fbref()
        elif scelta == "0":
            print("Chiusura Master Hub. A presto!\n")
            sys.exit()
        else:
            print("\n⚠️ Modulo non ancora attivo o scelta non valida.")

if __name__ == "__main__":
    menu_principale()