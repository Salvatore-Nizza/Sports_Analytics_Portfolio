import pandas as pd
import sys
import warnings

# Disattiviamo i warning fastidiosi per mantenere il terminale pulito
warnings.filterwarnings('ignore')

def menu_principale():
    print("\n" + "="*50)
    print(" 🏆 SPORTS ANALYTICS MASTER HUB 🏆")
    print("="*50)
    print("Scegli lo sport da cui estrarre i dati:")
    print(" 1. ⚽ Calcio (Dati Evento - StatsBomb)")
    print(" 2. ⚽ Calcio (Dati Aggregati - FBref/SoccerData)")
    print(" 3. 🏀 Basket (Statistiche NBA uffciali)")
    print(" 4. 🏎️ Motori (Telemetria Formula 1)")
    print(" 5. 🏈 Football Americano (NFL Play-by-Play)")
    print(" 6. ⚾ Baseball (MLB Statcast)")
    print(" 7. 🎾 Tennis (Database Storico ATP/WTA)")
    print(" 0. ❌ Esci dal programma")
    print("="*50)
    
    scelta = input("Inserisci il numero corrispondente e premi Invio: ")
    return scelta

def main():
    while True:
        scelta = menu_principale()

        if scelta == "1":
            print("\n>>> Avvio modulo CALCIO (StatsBomb) ...")
            from statsbombpy import sb
            
            print("Estrazione Finale Mondiali 2022 (Argentina - Francia)...")
            eventi_finale = sb.events(match_id=3869685)
            print(f"✅ Estratti {len(eventi_finale)} eventi!")
            print(eventi_finale[['minute', 'second', 'team', 'type', 'player']].head(5))
            
        elif scelta == "2":
            print("\n>>> Avvio modulo CALCIO AGGREGATO (SoccerData) ...")
            import soccerdata as sd
            
            print("Scaricamento classifica Serie A attuale da FBref...")
            fbref = sd.FBref(leagues="ITA-Serie A", seasons="2324")
            classifica = fbref.read_team_season_stats()
            print("✅ Dati estratti con successo!")
            # Stampa le prime righe
            print(classifica.head(3))

        elif scelta == "3":
            print("\n>>> Avvio modulo BASKET (NBA API) ...")
            from nba_api.stats.static import players
            from nba_api.stats.endpoints import playercareerstats
            
            print("Ricerca statistiche carriera di LeBron James...")
            giocatori = players.get_players()
            lebron = [player for player in giocatori if player['full_name'] == 'LeBron James'][0]
            carriera = playercareerstats.PlayerCareerStats(player_id=lebron['id']).get_data_frames()[0]
            print(f"✅ Dati estratti! Stagioni giocate trovate: {len(carriera)}")
            print(carriera[['SEASON_ID', 'TEAM_ABBREVIATION', 'PTS', 'AST', 'REB']].tail(3))

        elif scelta == "4":
            print("\n>>> Avvio modulo FORMULA 1 (FastF1) ...")
            import fastf1
            
            print("Estrazione calendario gare 2023...")
            calendario = fastf1.get_event_schedule(2023)
            print("✅ Calendario scaricato!")
            print(calendario[['RoundNumber', 'EventName', 'Location']].head(3))

        elif scelta in ["5", "6", "7"]:
            # Per non sovraccaricare lo script iniziale, qui prepariamo la struttura
            # che riempiremo quando deciderai di analizzare questi sport specifici.
            print(f"\n>>> Modulo {scelta} selezionato. Ambiente pronto per l'inserimento del codice di estrazione.")
            
        elif scelta == "0":
            print("\nUscita in corso. Alla prossima analisi! 📊\n")
            sys.exit()
            
        else:
            print("\n⚠️ Scelta non valida. Riprova inserendo un numero da 0 a 7.")

# Punto di ingresso dello script
if __name__ == "__main__":
    main()