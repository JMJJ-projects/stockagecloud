// JS pour la page de connexion 
document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const username = this.username.value;
    const password = this.password.value;
    const res = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (res.ok) {
        alert('Connexion réussie !');
        window.location.href = '/index.html';
        // Rediriger ou stocker l'utilisateur
    } else {
        alert(data.error || 'Erreur de connexion');
    }
}); 