import subprocess
import webbrowser
import sys

# Inserisci qui l'URL esatto della tua pagina GitHub
REPO_URL = "https://github.com/Salvatore-Nizza/Sports_Analytics_Portfolio"

def esegui_comando(comando):
    """Esegue un comando nel terminale e ne mostra il risultato."""
    try:
        risultato = subprocess.run(comando, shell=True, text=True, capture_output=True)
        if risultato.stdout:
            print(risultato.stdout.strip())
        if risultato.stderr:
            print(risultato.stderr.strip())
        return risultato.returncode == 0
    except Exception as e:
        print(f"❌ Errore critico: {e}")
        return False

def menu_git():
    print("\n" + "="*45)
    print(" 🐙 GESTORE GITHUB PERSONALE 🐙")
    print("="*45)
    print(" 1. 📥 SCARICA codice da GitHub (Pull)")
    print(" 2. 📤 CARICA codice su GitHub (Add + Commit + Push)")
    print(" 3. 🔍 Controlla lo stato dei file (Status)")
    print(" 4. 🌐 Apri il repository nel Browser")
    print(" 0. ❌ Esci")
    print("="*45)
    
    return input("Cosa desideri fare? Inserisci un numero: ")

def main():
    while True:
        scelta = menu_git()

        if scelta == "1":
            print("\n>>> Scaricamento aggiornamenti dal server in corso...")
            esegui_comando("git pull origin main")
            
        elif scelta == "2":
            print("\n>>> Preparazione al caricamento...")
            messaggio = input("Scrivi un breve messaggio per questo salvataggio (es. 'Aggiunto nuovo script'): ")
            
            # Se non scrivi nulla, usa un messaggio standard
            if not messaggio.strip():
                messaggio = "Aggiornamento automatico"
                
            print("\n>>> Impacchettamento file (git add .)...")
            esegui_comando("git add .")
            
            print(f"\n>>> Creazione del salvataggio (git commit)...")
            esegui_comando(f'git commit -m "{messaggio}"')
            
            print("\n>>> Spedizione su GitHub (git push)...")
            successo = esegui_comando("git push origin main")
            if successo:
                print("\n✅ Codice caricato su GitHub con successo!")
            
        elif scelta == "3":
            print("\n>>> Stato attuale del tuo codice locale:")
            esegui_comando("git status")
            
        elif scelta == "4":
            print(f"\n>>> Apertura di {REPO_URL} ...")
            webbrowser.open(REPO_URL)
            
        elif scelta == "0":
            print("\nChiusura gestore. Alla prossima!\n")
            sys.exit()
            
        else:
            print("\n⚠️ Scelta non valida, riprova.")

if __name__ == "__main__":
    main()