// JS pour la page d'inscription 
document.getElementById('registerForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const form = e.target;
    const username = form.username.value;
    const email = form.email.value;
    const password = form.password.value;

    const messageDiv = document.getElementById('form-message');
    messageDiv.textContent = ''; // Clear previous messages

    try {
        const res = await fetch('/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        const data = await res.json();
        if (res.ok) {
            messageDiv.textContent = 'Inscription réussie ! Redirection...';
            messageDiv.style.color = 'green';
            setTimeout(() => window.location.href = '/login', 1500);
        } else {
            messageDiv.textContent = data.error || "Erreur lors de l'inscription";
            messageDiv.style.color = 'red';
        }
    } catch (error) {
        messageDiv.textContent = "Erreur réseau. Veuillez réessayer.";
        messageDiv.style.color = 'red';
    }
});
