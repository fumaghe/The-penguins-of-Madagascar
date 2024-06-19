from app.config import redis_client

def search_users(query):
    keys = redis_client.keys(f"user:*{query}*")
    users = [key.decode('utf-8').split(":")[1] for key in keys]
    return users

def add_contact(username, contact_username):
    if not redis_client.exists(f"user:{contact_username}"):
        return "Utente non trovato"
    redis_client.sadd(f"contacts:{username}", contact_username)
    return "Contatto aggiunto"