import pandas as pd # type: ignore
import sys
import warnings
from sqlalchemy import create_engine # type: ignore

warnings.filterwarnings('ignore')

def salva_su_database(df, nome_tabella):
    print(f"Tentativo di connessione al database per la tabella '{nome_tabella}'...")
    try:
        # STRINGA DI CONNESSIONE: postgresql://utente:password@host:porta/nome_database
        # Inserisci la tua password al posto di TUA_PASSWORD_QUI
        stringa_connessione = 'postgresql://postgres:sportanalytics@localhost:5432/sports_analytics'
        engine = create_engine(stringa_connessione)
        
        # Scrive il dataframe su SQL. if_exists='replace' sovrascrive la tabella se esiste già
        df.to_sql(nome_tabella, engine, if_exists='replace', index=False)
        print(f"✅ SUCCESSO! {len(df)} righe salvate in PostgreSQL nella tabella '{nome_tabella}'.")
    except Exception as e:
        print(f"❌ Errore durante il salvataggio: {e}")

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
    from statsbombpy import sb # type: ignore
    
    print("Estrazione Finale Mondiali 2022...")
    df_eventi = sb.events(match_id=3869685)
    print(f"✅ Estratti {len(df_eventi)} eventi.")
    
    # PULIZIA DATI BASE (SQL non ama liste o dizionari annidati nelle celle)
    # Convertiamo tutte le colonne complesse in stringhe per evitare errori
    for colonna in df_eventi.columns:
        if df_eventi[colonna].apply(type).eq(list).any() or df_eventi[colonna].apply(type).eq(dict).any():
            df_eventi[colonna] = df_eventi[colonna].astype(str)

    salva_su_database(df_eventi, nome_tabella="statsbomb_eventi_mondiale")

def modulo_fbref():
    print("\n>>> Avvio Modulo FBref (SoccerData)...")
    import soccerdata as sd # type: ignore
    
    print("Scaricamento classifica Serie A...")
    fbref = sd.FBref(leagues="ITA-Serie A", seasons="2324")
    df_classifica = fbref.read_team_season_stats()
    
    # Soccerdata crea indici complessi, li resettiamo per renderli compatibili con SQL
    df_classifica = df_classifica.reset_index()
    # Rinominiamo le colonne per eliminare gli spazi vuoti o caratteri strani
    df_classifica.columns = ['_'.join(col).strip() if isinstance(col, tuple) else str(col) for col in df_classifica.columns]
    
    print("✅ Dati estratti e puliti.")
    salva_su_database(df_classifica, nome_tabella="fbref_classifica_seriea")

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