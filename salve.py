<!DOCTYPE html>
<html>
<head>
    <title>Chat con {{ contact }}</title>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', (event) => {
            var socket = io();
            var room = "{{ room }}";
            var username = "{{ username }}";

            socket.emit('join', {username: username, room: room});

            socket.on('message', function(data) {
                var messages = document.getElementById('messages');
                var message = document.createElement('li');
                message.innerText = data;
                messages.appendChild(message);
            });

            socket.on('error', function(data) {
                alert(data.msg);
            });

            document.getElementById('send').onclick = function() {
                var message = document.getElementById('message').value;
                socket.emit('message', {room: room, message: message, username: username, contact: "{{ contact }}"});
                document.getElementById('message').value = '';
            };
        });
    </script>
</head>
<body>
    <h1>Chat con {{ contact }}</h1>
    <ul id="messages">
        {% for message in messages %}
        <li>{{ message }}</li>
        {% endfor %}
    </ul>
    <input type="text" id="message" placeholder="Enter message">
    <button id="send">Send</button>
    <br>
    <a href="{{ url_for('home') }}">Torna alla Home</a>
</body>
</html>