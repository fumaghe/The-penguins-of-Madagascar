# The-penguins-of-Madagascar

Funzioni
Registrare un utente:
curl -X POST http://127.0.0.1:5000/register -H "Content-Type: application/json" -d '{"username": "user1", "password": "pass1"}'

Effettuare il login:
curl -X POST http://127.0.0.1:5000/login -H "Content-Type: application/json" -d '{"username": "user1", "password": "pass1"}'

Cercare utenti:
curl http://127.0.0.1:5000/search?query=user


Aggiungere un contatto:
curl -X POST http://127.0.0.1:5000/add_contact -H "Content-Type: application/json" -d '{"contact": "user2"}' -b cookie.txt
Assicurati di aver eseguito il login prima di aggiungere un contatto.

Impostare la modalità Do Not Disturb:
curl -X POST http://127.0.0.1:5000/set_dnd -H "Content-Type: application/json" -d '{"dnd": "true"}' -b cookie.txt
Inviare un messaggio:

bash
Copia codice
curl -X POST http://127.0.0.1:5000/send_message -H "Content-Type: application/json" -d '{"recipient": "user2", "message": "Hello"}' -b cookie.txt
Recuperare una chat:

bash
Copia codice
curl http://127.0.0.1:5000/get_chat?contact=user2 -b cookie.txt