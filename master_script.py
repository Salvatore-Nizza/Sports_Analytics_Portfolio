import pandas as pd
import sys
import warnings

warnings.filterwarnings('ignore')

def menu_principale():
    print("\n" + "="*50)
    print(" 🏆 SPORTS ANALYTICS MASTER HUB 🏆")
    print("="*50)
    print("Scegli il database da interrogare:")
    print(" 1. ⚽ Calcio: StatsBomb (Dati Evento)")
    print(" 2. ⚽ Calcio: FBref/SoccerData (Dati Aggregati)")
    print(" 3. 🏀 Basket: NBA API (In lavorazione 🚧)")
    print(" 4. 🏎️ Motori: FastF1 (In lavorazione 🚧)")
    print(" 5. 🏈 Football: NFL Play-by-Play (In lavorazione 🚧)")
    print(" 6. ⚾ Baseball: MLB Statcast (In lavorazione 🚧)")
    print(" 7. 🎾 Tennis: ATP/WTA Storico (In lavorazione 🚧)")
    print(" 0. ❌ Esci")
    print("="*50)
    
    return input("Inserisci il numero e premi Invio: ")

def modulo_statsbomb():
    print("\n>>> Avvio Modulo StatsBomb...")
    from statsbombpy import sb
    
    # Per ora estraiamo i dati di una partita fissa, 
    # poi aggiungeremo l'opzione per scegliere la lega/stagione.
    print("Estrazione Finale Mondiali 2022...")
    df_eventi = sb.events(match_id=3869685)
    print(f"✅ Estratti {len(df_eventi)} eventi.")
    
    # Questa è la funzione che creeremo nel prossimo step!
    # salva_su_database(df_eventi, nome_tabella="statsbomb_eventi_prova")

def modulo_fbref():
    print("\n>>> Avvio Modulo FBref (SoccerData)...")
    import soccerdata as sd
    
    print("Scaricamento classifica Serie A...")
    fbref = sd.FBref(leagues="ITA-Serie A", seasons="2324")
    df_classifica = fbref.read_team_season_stats()
    print("✅ Dati estratti.")
    
    # salva_su_database(df_classifica, nome_tabella="fbref_classifica_prova")

def main():
    while True:
        scelta = menu_principale()

        if scelta == "1":
            modulo_statsbomb()
        elif scelta == "2":
            modulo_fbref()
        elif scelta in ["3", "4", "5", "6", "7"]:
            print(f"\n⚠️ Modulo {scelta} attualmente in fase di sviluppo. Riprova più avanti!")
        elif scelta == "0":
            print("\nUscita. A presto!\n")
            sys.exit()
        else:
            print("\n❌ Scelta non valida.")

if __name__ == "__main__":
    main()