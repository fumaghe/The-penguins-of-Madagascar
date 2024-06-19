from flask import Flask, render_template, request, redirect, url_for, session
import redis

app = Flask(__name__)
app.secret_key = 'supersecretkey'

r = redis.Redis(host='localhost', port=6379, db=0)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    stored_password = r.get(username)
    if stored_password and stored_password.decode('utf-8') == password:
        session['username'] = username
        return redirect(url_for('chat'))
    else:
        return 'Invalid credentials'

@app.route('/chat')
def chat():
    if 'username' in session:
        return f'Welcome {session["username"]} to the chat!'
    else:
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)