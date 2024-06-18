document.addEventListener('DOMContentLoaded', () => {
    console.log('Script loaded');

    const loginBtn = document.getElementById('login-btn');
    loginBtn.addEventListener('click', () => {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        // Esegui la logica di login qui...
        console.log('Username:', username);
        console.log('Password:', password);
    });
});

