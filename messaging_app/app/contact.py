from app.config import redis_client

def set_dnd(username, dnd_status):
    redis_client.hset(f"user:{username}", "dnd", dnd_status)
    return "Stato DnD aggiornato"