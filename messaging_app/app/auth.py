from app.utils import hash_password, verify_password
from app.config import redis_client

def register_user(username, password):
    if redis_client.exists(f"user:{username}"):
        return "Nome utente già esistente"
    hashed_password = hash_password(password)
    redis_client.hmset(f"user:{username}", {"username": username, "password": hashed_password})
    return "Registrazione completata"

def authenticate_user(username, password):
    user = redis_client.hgetall(f"user:{username}")
    if not user:
        return "Utente non trovato"
    if verify_password(password, user[b'password'].decode('utf-8')):
        return "Autenticazione riuscita"
    else:
        return "Password errata"