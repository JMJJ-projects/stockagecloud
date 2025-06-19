// JS pour la page de connexion
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('loginForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const form = e.target;
        const username = form.username.value;
        const password = form.password.value;
        const messageDiv = document.getElementById('form-message');
        messageDiv.textContent = '';

        try {
            const res = await fetch('/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();
            if (res.ok) {
                messageDiv.textContent = 'Connexion réussie ! Redirection...';
                messageDiv.style.color = 'green';
                setTimeout(() => window.location.href = '/dashboard', 1000);
            } else {
                messageDiv.textContent = data.error || 'Erreur de connexion';
                messageDiv.style.color = 'red';
            }
        } catch (error) {
            messageDiv.textContent = "Erreur réseau. Veuillez réessayer.";
            messageDiv.style.color = 'red';
        }
    });
});
document.getElementById('registerButton').addEventListener('click', async function(e) {
             window.location.href = '/register'
});
