import redis
import hashlib
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, join_room, send, emit
import datetime

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
            return "Nome utente non trovato. Riprova."
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if r.exists(username):
            return "Nome utente già esistente. Scegli un nome diverso."
        else:
            user_data = {"username": username, "password": hash_password(password), "dnd": "false"}
            r.hset(username, mapping=user_data)
            session['username'] = username
            return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    contacts = get_contacts(username)
    return render_template('home.html', username=username, contacts=contacts)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/add_contact', methods=['GET', 'POST'])
def add_contact():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = session['username']
        new_contact = request.form['new_contact']
        if r.exists(new_contact):
            add_contact_to_book(username, new_contact)
            return redirect(url_for('home'))
        else:
            return "Utente non trovato."
    return render_template('add_contact.html')

@app.route('/remove_contact', methods=['GET', 'POST'])
def remove_contact():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = session['username']
        contact_to_remove = request.form['contact_to_remove']
        remove_contact_from_book(username, contact_to_remove)
        return redirect(url_for('home'))
    return render_template('remove_contact.html')

@app.route('/contacts')
def contacts():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    contacts = get_contacts(username)
    return render_template('contacts.html', contacts=contacts)

@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        search_query = request.form['search_query']
        results = search_users(search_query)
        return render_template('search_results.html', results=results)
    return render_template('search.html')

@app.route('/dnd', methods=['POST'])
def toggle_dnd():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    user_data = r.hgetall(username)
    new_dnd_status = "true" if user_data["dnd"] == "false" else "false"
    r.hset(username, "dnd", new_dnd_status)
    return redirect(url_for('home'))

@app.route('/chat/<contact>')
def chat(contact):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    room = get_room_name(username, contact)
    messages = get_chat_messages(room)
    return render_template('chat.html', username=username, contact=contact, messages=messages, room=room)

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    send(username + ' has entered the room.', to=room)

@socketio.on('message')
def on_message(data):
    room = data['room']
    message = data['message']
    username = data['username']
    contact = data['contact']
    chat_key = f"{room}_chat"

    contact_data = r.hgetall(contact)
    if contact_data.get("dnd") == "true":
        emit('error', {'msg': 'L\'utente è in modalità Do Not Disturb.'}, to=request.sid)
    else:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"{timestamp} > {username}: {message}"
        r.rpush(chat_key, formatted_message)
        send(formatted_message, to=room)

def get_contacts(username):
    contacts_key = f"{username}_contacts"
    if not r.exists(contacts_key):
        r.rpush(contacts_key, username)
    contacts = r.lrange(contacts_key, 0, -1)
    return contacts

def add_contact_to_book(username, new_contact):
    contacts_key = f"{username}_contacts"
    r.rpush(contacts_key, new_contact)

def remove_contact_from_book(username, contact_to_remove):
    contacts_key = f"{username}_contacts"
    r.lrem(contacts_key, 0, contact_to_remove)

def search_users(query):
    all_users = r.keys('*')
    matching_users = [user for user in all_users if query in user]
    return matching_users

def get_room_name(username, contact):
    participants = sorted([username, contact])
    return f"{participants[0]}_{participants[1]}"

def get_chat_messages(room):
    chat_key = f"{room}_chat"
    return r.lrange(chat_key, 0, -1)

if __name__ == '__main__':
    socketio.run(app, debug=True)   