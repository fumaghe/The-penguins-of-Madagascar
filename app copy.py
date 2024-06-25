from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_socketio import SocketIO, join_room, send, emit
import redis
import hashlib
import datetime
import threading
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'
socketio = SocketIO(app)


# Connessione a Redis
try:
    r = redis.Redis(
        host='redis-17465.c328.europe-west3-1.gce.redns.redis-cloud.com',
        port=17465, db=0, charset="utf-8", decode_responses=True,
        password="FbLFAtUtlUz7j436R9kA0OkAYNUzZMi6"
    )
    r.ping()  # Controlla la connessione
    print("Connessione a Redis riuscita!")
except redis.ConnectionError as e:
    print(f"Errore di connessione a Redis: {e}")
    exit(1)

# Funzione per hashing della password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Percorso della cartella di upload
UPLOAD_FOLDER = r'C:\Users\AndreaFumagalli\OneDrive - ITS Angelo Rizzoli\Documenti\GitHub\The-penguins-of-Madagascar\static\avatars'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DEFAULT_AVATAR = 'foto profilo.png'

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if r.exists(username):
            user_data = r.hgetall(username)
            if user_data.get("password") == hash_password(password):
                session['username'] = username
                return redirect(url_for('home'))
            else:
                error = "Password errata. Riprova."
        else:
            error = "Nome utente non trovato. Riprova."
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            error = "Le password non corrispondono. Riprova."
        elif r.exists(username):
            error = "Nome utente già esistente. Scegli un nome diverso."
        else:
            avatar = request.files.get('avatar')
            if avatar and avatar.filename != '':
                filename = secure_filename(f"{username}.png")
                avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                avatar.save(avatar_path)
            else:
                filename = 'foto profilo.png'  # Immagine predefinita

            user_data = {
                "username": username,
                "password": hash_password(password),
                "dnd": "false",
                "avatar": filename  # Salva solo il nome del file
            }
            r.hset(username, mapping=user_data)
            session['username'] = username
            return redirect(url_for('home'))
    return render_template('register.html', error=error)

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    contacts = get_contacts(username)
    dnd = r.hget(username, 'dnd')
    avatar = r.hget(username, 'avatar')
    auto_delete = r.hget(username, 'auto_delete')
    return render_template('home.html', username=username, contacts=contacts, dnd=dnd, avatar=avatar, auto_delete=auto_delete)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/add_contact', methods=['POST'])
def add_contact():
    if 'username' not in session:
        return jsonify({"status": "error", "message": "Non sei autenticato"}), 401
    username = session['username']
    new_contact = request.form['new_contact']
    if r.exists(new_contact):
        add_contact_to_book(username, new_contact)
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Utente non trovato"}), 404

@app.route('/remove_contact', methods=['POST'])
def remove_contact():
    if 'username' not in session:
        return jsonify({"status": "error", "message": "Non sei autenticato"}), 401
    username = session['username']
    contact_to_remove = request.form['contact_to_remove']
    remove_contact_from_book(username, contact_to_remove)
    return jsonify({"status": "success"})

@app.route('/toggle_dnd', methods=['POST'])
def toggle_dnd():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    user_data = r.hgetall(username)
    new_dnd_status = "true" if user_data["dnd"] == "false" else "false"
    r.hset(username, "dnd", new_dnd_status)
    
    # Notify all users about the DND status change
    dnd_message = f"Il destinatario ha attivato la modalità non disturbare" if new_dnd_status == "true" else f"{username} ha disattivato la modalità non disturbare"
    socketio.emit('dnd_status_change', {'message': dnd_message, 'username': 'system'}, broadcast=True)
    
    return redirect(url_for('home'))
    
@app.route('/toggle_auto_delete', methods=['POST'])
def toggle_auto_delete():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    user_data = r.hgetall(username)
    new_auto_delete_status = "true" if user_data.get("auto_delete", "false") == "false" else "false"
    r.hset(username, "auto_delete", new_auto_delete_status)
    return redirect(url_for('home'))

@app.route('/profile', methods=['POST'])
def update_profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    current_username = session['username']
    new_username = request.form.get('new_username', current_username)
    new_password = request.form.get('new_password')
    avatar = request.files.get('avatar')

    # Recupera i dati attuali dell'utente
    user_data = r.hgetall(current_username)
    
    # Aggiorna il nome utente se fornito
    if new_username and new_username != current_username:
        user_data['username'] = new_username

    # Aggiorna la password se fornita
    if new_password:
        user_data['password'] = hash_password(new_password)
    
    # Aggiorna l'avatar se fornito
    if avatar and avatar.filename != '':
        filename = secure_filename(f"{new_username}.png")
        avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        avatar.save(avatar_path)
        user_data['avatar'] = filename  # Aggiorna solo il nome del file dell'avatar

    # Verifica che l'avatar esistente non venga rimosso
    if 'avatar' not in user_data:
        user_data['avatar'] = 'foto profilo.png'

    # Aggiorna i dati dell'utente in Redis
    r.hset(current_username, mapping=user_data)

    # Se il nome utente è cambiato, rinomina la chiave in Redis
    if new_username and new_username != current_username:
        r.rename(current_username, new_username)
        session['username'] = new_username

    return redirect(url_for('home'))



@app.route('/chat/<contact>')
def chat(contact):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    room = get_room_name(username, contact)
    messages = get_chat_messages(room)
    return jsonify({'messages': messages})

@app.route('/search', methods=['POST'])
def search():
    if 'username' not in session:
        return redirect(url_for('login'))
    search_query = request.form['search_query']
    results = search_users(search_query)
    return jsonify({"results": results})

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    send({'message': f'{username} has entered the room.', 'username': 'system'}, to=room)

@socketio.on('message')
def on_message(data):
    room = data['room']
    message = data['message']
    username = data['username']
    contact = data['contact']
    chat_key = f"{room}_chat"

    user_data = r.hgetall(username)
    contact_data = r.hgetall(contact)
    
    if user_data.get("dnd") == "true":
        emit('error', {'msg': 'Hai attivato la modalità Do Not Disturb.'}, to=request.sid)
        return

    if contact_data.get("dnd") == "true":
        emit('error', {'msg': 'Il destinatario è in modalità Do Not Disturb.'}, to=request.sid)
        return

    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    auto_delete = r.hget(username, "auto_delete") == "true"
    formatted_message = f"{timestamp} > {username}: {message}"
    r.rpush(chat_key, formatted_message)
    send({'message': message, 'username': username, 'timestamp': timestamp, 'auto_delete': auto_delete}, to=room)

    # Emit to update the last message in the sidebar
    emit('update_last_message', {'contact': contact, 'last_message': message}, broadcast=True)

    if auto_delete:
        timer = threading.Timer(60.0, delete_message, args=[chat_key, formatted_message, room])
        timer.start()

def delete_message(chat_key, message, room):
    r.lrem(chat_key, 0, message)
    # Notify clients to remove the message
    send({'message': message, 'delete': True}, to=room)

def get_last_message(username, contact):
    room = get_room_name(username, contact)
    chat_key = f"{room}_chat"
    last_message = r.lrange(chat_key, -1, -1)
    if last_message:
        parts = last_message[0].split(' > ', 1)
        if len(parts) == 2:
            timestamp, text = parts
            sender, message = text.split(': ', 1)
            return message
    return "..."

def get_contacts(username):
    contacts_key = f"{username}_contacts"
    if not r.exists(contacts_key):
        r.rpush(contacts_key, username)
    contacts = r.lrange(contacts_key, 0, -1)
    contact_list = []
    for contact in contacts:
        last_message = get_last_message(username, contact)
        avatar = r.hget(contact, 'avatar') or 'static/default-avatar.png'
        contact_list.append({'name': contact, 'last_message': last_message, 'avatar': avatar})
    return contact_list

def add_contact_to_book(username, new_contact):
    contacts_key = f"{username}_contacts"
    r.rpush(contacts_key, new_contact)

def remove_contact_from_book(username, contact_to_remove):
    contacts_key = f"{username}_contacts"
    r.lrem(contacts_key, 0, contact_to_remove)

def get_room_name(username, contact):
    participants = sorted([username, contact])
    return f"{participants[0]}_{participants[1]}"

def get_chat_messages(room):
    chat_key = f"{room}_chat"
    messages = r.lrange(chat_key, 0, -1)
    message_list = []
    for msg in messages:
        parts = msg.split(' > ', 1)
        if len(parts) == 2:
            timestamp, text = parts
            sender, message = text.split(': ', 1)
            message_list.append({'timestamp': timestamp, 'sender': sender, 'text': message})
    return message_list

def search_users(query):
    keys = r.keys(f"*{query}*")
    users = [key for key in keys if r.type(key) == 'hash']
    return users

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
