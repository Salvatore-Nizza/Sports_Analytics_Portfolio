from statsbombpy import sb
import pandas as pd

# 1. ESPLORAZIONE: Scarichiamo l'elenco di tutte le competizioni gratuite disponibili
print("--- SCARICAMENTO COMPETIZIONI ---")
competizioni = sb.competitions()
# Mostriamo solo le colonne più interessanti per capire come sono organizzati i dati
print(competizioni[['competition_id', 'competition_name', 'season_name']].head(15))


# 2. RICERCA PARTITE: Prendiamo le partite dei Mondiali 2022
# Dai dati sopra sappiamo che la FIFA World Cup ha l'ID 43 e la stagione 2022 ha l'ID 106
print("\n--- SCARICAMENTO PARTITE MONDIALI 2022 ---")
partite_mondiale = sb.matches(competition_id=43, season_id=106)
print(partite_mondiale[['match_id', 'home_team', 'away_team', 'match_date']].head())


# 3. ESTRAZIONE DATI DI EVENTO: La finale Argentina - Francia
# L'ID della finale è 3869685. Chiediamo a StatsBomb TUTTI gli eventi di quella partita.
print("\n--- ESTRAZIONE EVENTI ARGENTINA VS FRANCIA ---")
eventi_finale = sb.events(match_id=3869685)

# Mostriamo quanti eventi sono stati estratti e le prime 10 azioni della partita
print(f"La libreria ha scaricato {len(eventi_finale)} eventi per questa singola partita!")
print("\nLe primissime azioni del match:")
print(eventi_finale[['minute', 'second', 'team', 'type', 'player']].head(10))