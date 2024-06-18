document.addEventListener('DOMContentLoaded', () => {
    console.log('Script loaded');

    const loginBtn = document.getElementById('login-btn');
    loginBtn.addEventListener('click', () => {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        fetch('/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        })
        .then(response => {
            if (!response.ok) {
                throw Error(response.statusText);
            }
            return response.json();
        })
        .then(data => {
            alert(data.message);
            // Esegui le azioni successive al login
        })
        .catch(error => {
            alert('Login failed. Invalid username or password.');
            console.error('Error:', error);
        });
    });
});