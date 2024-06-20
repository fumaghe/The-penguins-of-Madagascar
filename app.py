import redis
import threading
import time
import hashlib
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, send

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Cambia questa chiave con una chiave segreta sicura
socketio = SocketIO(app)

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

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if r.exists(username):
            user_data = r.hgetall(username)
            if user_data.get("password") == hash_password(password):
                session['username'] = username
                return redirect(url_for('home'))
            else:
                return "Password errata. Riprova."
        else:
            user_data = {"username": username, "password": hash_password(password)}
            r.hset(username, mapping=user_data)
            session['username'] = username
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    return render_template('home.html', username=username)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    send(username + ' has entered the room.', to=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    send(username + ' has left the room.', to=room)

@socketio.on('message')
def on_message(data):
    room = data['room']
    message = data['message']
    username = data['username']
    chat_key = f"{room}_chat"
    r.rpush(chat_key, f"{username}: {message}")
    send(username + ": " + message, to=room)

@socketio.on('load_messages')
def load_messages(data):
    room = data['room']
    chat_key = f"{room}_chat"
    messages = r.lrange(chat_key, 0, -1)
    for message in messages:
        send(message, to=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)