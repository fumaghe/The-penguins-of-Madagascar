import datetime
from app.config import redis_client

def send_message(sender, receiver, message):
    if redis_client.hget(f"user:{receiver}", "dnd") == "1":
        return "!! IMPOSSIBILE RECAPITARE IL MESSAGGIO, L’UTENTE HA LA MODALITA’ DnD ATTIVA"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    redis_client.rpush(f"chat:{sender}:{receiver}", f">{message}\t[{timestamp}]")
    redis_client.rpush(f"chat:{receiver}:{sender}", f"<{message}\t[{timestamp}]")
    return "Messaggio inviato"

def get_messages(username, contact):
    messages = redis_client.lrange(f"chat:{username}:{contact}", 0, -1)
    return [message.decode('utf-8') for message in messages]