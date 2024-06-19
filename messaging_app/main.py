from app.auth import register_user, authenticate_user
from app.user import search_users, add_contact
from app.message import send_message, get_messages
from app.contact import set_dnd

def main():
    while True:
        print("1. Registrati")
        print("2. Login")
        print("3. Esci")
        choice = input("Scegli un'opzione: ")

        if choice == "1":
            username = input("Nome utente: ")
            password = input("Password: ")
            print(register_user(username, password))
        elif choice == "2":
            username = input("Nome utente: ")
            password = input("Password: ")
            if authenticate_user(username, password) == "Autenticazione riuscita":
                print("Login riuscito")
                while True:
                    print("\n1. Cerca utenti")
                    print("2. Aggiungi contatto")
                    print("3. Imposta DnD")
                    print("4. Invia messaggio")
                    print("5. Leggi messaggi")
                    print("6. Logout")
                    user_choice = input("Scegli un'opzione: ")

                    if user_choice == "1":
                        query = input("Inserisci nome utente da cercare: ")
                        users = search_users(query)
                        print("Utenti trovati: ", users)
                    elif user_choice == "2":
                        contact_username = input("Nome utente del contatto: ")
                        print(add_contact(username, contact_username))
                    elif user_choice == "3":
                        dnd_status = input("Imposta DnD (1 per attivare, 0 per disattivare): ")
                        print(set_dnd(username, dnd_status))
                    elif user_choice == "4":
                        receiver = input("Nome utente del destinatario: ")
                        message = input("Messaggio: ")
                        print(send_message(username, receiver, message))
                    elif user_choice == "5":
                        contact = input("Nome utente del contatto: ")
                        messages = get_messages(username, contact)
                        for message in messages:
                            print(message)
                    elif user_choice == "6":
                        break
            else:
                print("Autenticazione fallita")
        elif choice == "3":
            break

if __name__ == "__main__":
    main()