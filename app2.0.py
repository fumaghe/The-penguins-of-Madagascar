import redis
import threading
import time
import hashlib

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

# Funzione per hashing della password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Funzione per gestire il login
def login(username):
    while True:
        if r.exists(username):
            # L'utente esiste già, chiedi la password
            user_data = r.hgetall(username)
            password = input("Inserisci la password: ")
            if user_data.get("password") == hash_password(password):
                return user_data
            else:
                print("Password errata. Riprova.")
        else:
            # Nuovo utente, crea una nuova chiave e chiedi la password
            password = input("Crea una nuova password: ")
            user_data = {"username": username, "password": hash_password(password)}
            r.hset(username, mapping=user_data)
            return user_data

# Funzione per gestire l'interazione utente
def menu_interattivo():
    while True:
        username = input("Inserisci il tuo username: ")
        user_data = login(username)
        if user_data:
            print(f"Benvenuto, {username}!")

            while True:
                print("\n=========================")
                print("Operazioni disponibili:")
                print("1. Mostra rubrica")
                print("2. Aggiungi contatto")
                print("3. Rimuovi contatto")
                print("4. Invia/Leggi messaggi")
                print("5. Apri chat")
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
                    chat_completa(username, destinatario)

                elif scelta == "5":
                    destinatario = input("Inserisci il nome del destinatario: ")
                    chat_completa(username, destinatario)

                elif scelta == "e":
                    print("Grazie per aver usato il servizio. Arrivederci!")
                    break

                else:
                    print("Scelta non valida. Riprova.")
        else:
            print("Accesso negato. Riprova.")

# Funzione per gestire la rubrica
def rubrica(username):
    rubrica_key = f"{username}_rubrica"
    if not r.exists(rubrica_key):
        r.rpush(rubrica_key, username)
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

# Funzione per visualizzare messaggi storici e inviare nuovi messaggi
def chat_completa(mittente, destinatario):
    lista = [mittente, destinatario]
    lista.sort()
    chat_key = f"{lista[0]}_{lista[1]}"
    
    # Visualizza messaggi storici
    messaggi = r.lrange(chat_key, 0, -1)
    print(f"\nChat tra {mittente} e {destinatario}:")
    for messaggio in messaggi:
        print(messaggio)

    # Funzione per aggiornare la chat in tempo reale
    def aggiorna_chat(stop_event):
        ultimo_messaggio = len(messaggi)
        while not stop_event.is_set():
            time.sleep(2)
            nuovi_messaggi = r.lrange(chat_key, ultimo_messaggio, -1)
            for messaggio in nuovi_messaggi:
                print(messaggio)
            ultimo_messaggio += len(nuovi_messaggi)

    stop_event = threading.Event()
    thread = threading.Thread(target=aggiorna_chat, args=(stop_event,), daemon=True)
    thread.start()

    while True:
        messaggio = input(f"Inserisci il messaggio da inviare a '{destinatario}' (o 'q' per uscire): ")
        if messaggio.lower() == 'q':
            stop_event.set()
            thread.join()
            break
        r.rpush(chat_key, f"{mittente}: {messaggio}")

# Avvio del programma
if __name__ == "__main__":
    menu_interattivo()