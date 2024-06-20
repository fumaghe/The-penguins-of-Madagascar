import redis
import threading
import time

# Connessione a Redis
try:
    r = redis.Redis(host='redis-17465.c328.europe-west3-1.gce.redns.redis-cloud.com',
                    port=17465, db=0, charset="utf-8", decode_responses=True,
                    password="FbLFAtUtlUz7j436R9kA0OkAYNUzZMi6")
    r.ping()  # Controlla la connessione
    print("Connessione a Redis riuscita!")
except redis.ConnectionError as e:
    print(f"Errore di connessione a Redis: {e}")
    exit(1)

# Funzione per gestire il login
def login(username):
    if r.exists(username):
        # L'utente esiste già, chiedi la password
        user_data = r.hgetall(username)
        password = input("Inserisci la password: ")
        if user_data.get("password") == password:
            return user_data
        else:
            print("Password errata.")
            return None
    else:
        # Nuovo utente, crea una nuova chiave e chiedi la password
        password = input("Crea una nuova password: ")
        user_data = {"username": username, "password": password}
        r.hmset(username, user_data)
        return user_data

# Funzione per gestire l'interazione utente
def menu_interattivo():
    username = input("Inserisci il tuo username: ")
    user_data = login(username)
    if user_data:
        print(f"Benvenuto, {username}!")

        while True:
            print("")
            print("=========================")
            print("Operazioni disponibili:")
            print("1. Mostra rubrica")
            print("2. Aggiungi contatto")
            print("3. Rimuovi contatto")
            print("4. Invia/Leggi messaggi")
            print("e. Esci")
            print("=========================")

            scelta = input("Inserisci il numero dell'operazione da eseguire o 'e' per uscire: ")

            if scelta == "1":
                contatti = rubrica(username)
                print(f"Rubrica di {username}:")
                for contatto in contatti:
                    print(contatto)

            elif scelta == "2":
                nuovo_contatto = input("Inserisci il nome del nuovo contatto da aggiungere: ")
                aggiungi_contatto(username, nuovo_contatto)
                print(f"Contatto '{nuovo_contatto}' aggiunto alla rubrica.")

            elif scelta == "3":
                contatto_da_rimuovere = input("Inserisci il nome del contatto da rimuovere: ")
                rimuovi_contatto(username, contatto_da_rimuovere)
                print(f"Contatto '{contatto_da_rimuovere}' rimosso dalla rubrica.")

            elif scelta == "4":
                destinatario = input("Inserisci il nome del destinatario: ")
                chat_messaggi(username, destinatario)

            elif scelta == "e":
                print("Grazie per aver usato il servizio. Arrivederci!")
                break

            else:
                try:
                    scelta_numerica = int(scelta)
                    print("Scelta non valida. Riprova.")
                except ValueError:
                    print("Scelta non valida. Riprova.")

    else:
        print("Accesso negato.")

# Funzione per gestire la rubrica
def rubrica(username):
    # Crea una chiave per la rubrica dell'utente
    rubrica_key = f"{username}_rubrica"

    # Se la rubrica non esiste, creala
    if not r.exists(rubrica_key):
        r.rpush(rubrica_key, username)

    # Restituisci la lista di contatti nella rubrica
    contatti = r.lrange(rubrica_key, 0, -1)
    return contatti

# Funzione per aggiungere un contatto alla rubrica
def aggiungi_contatto(username, nuovo_contatto):
    rubrica_key = f"{username}_rubrica"
    r.rpush(rubrica_key, nuovo_contatto)

# Funzione per rimuovere un contatto dalla rubrica
def rimuovi_contatto(username, contatto_da_rimuovere):
    rubrica_key = f"{username}_rubrica"
    r.lrem(rubrica_key, 0, contatto_da_rimuovere)

# Funzione per inviare e leggere messaggi
def chat_messaggi(mittente, destinatario):
    lista = [mittente, destinatario]
    lista.sort()
    chat_key = f"{lista[0]}_{lista[1]}"

    def aggiorna_chat():
        ultimo_messaggio = len(r.lrange(chat_key, 0, -1))
        while True:
            time.sleep(2)
            messaggi = r.lrange(chat_key, 0, -1)
            if len(messaggi) > ultimo_messaggio:
                nuovi_messaggi = messaggi[ultimo_messaggio:]
                for messaggio in nuovi_messaggi:
                    print(messaggio)
                ultimo_messaggio = len(messaggi)

    threading.Thread(target=aggiorna_chat, daemon=True).start()

    while True:
        messaggio = input(f"Inserisci il messaggio da inviare a '{destinatario}' (o 'q' per uscire): ")
        if messaggio.lower() == 'q':
            break
        r.rpush(chat_key, f"{mittente}: {messaggio}")

# Avvio del programma
if __name__ == "__main__":
    menu_interattivo()