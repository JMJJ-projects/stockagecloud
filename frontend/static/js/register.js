// JS pour la page d'inscription 
document.getElementById('registerForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const username = this.username.value;
    const email = this.email.value;
    const password = this.password.value;
    const res = await fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password })
    });
    const data = await res.json();
    if (res.ok) {
        alert('Inscription réussie !');
        window.location.href = '/login.html';
    } else {
        alert(data.error || 'Erreur lors de l\'inscription');
    }
}); 