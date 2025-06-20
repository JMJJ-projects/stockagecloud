// Display feedback messages in the dashboard
function showMessage(msg, type='info') {
    const msgDiv = document.getElementById('dashboard-message');
    if (!msgDiv) return;
    msgDiv.textContent = msg;
    msgDiv.style.color = (type === 'success') ? 'green' : (type === 'error') ? 'red' : 'black';
    setTimeout(() => { msgDiv.textContent = ''; }, 3000);
}

// AJAX file upload (optional, fallback to classic form if JS fails)
const uploadForm = document.querySelector('form[action$="dashboard"]');
if (uploadForm) {
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const fileInput = uploadForm.querySelector('input[type="file"]');
        if (!fileInput.files.length) {
            showMessage("Veuillez sélectionner un fichier.", "error");
            return;
        }
        const formData = new FormData(uploadForm);
        try {
            const res = await fetch(uploadForm.action, {
                method: 'POST',
                body: formData
            });
            let text = '';
            try {
                text = await res.text();
            } catch (err) {
                showMessage("Réponse serveur invalide.", "error");
                return;
            }
            if (res.redirected) {
                window.location.href = res.url; // For Flask redirect after upload
                return;
            }
            if (res.ok) {
                showMessage("Fichier téléversé !", "success");
                setTimeout(() => window.location.reload(), 1000);
            } else {
                showMessage(text || "Erreur lors du téléversement.", "error");
            }
        } catch (err) {
            showMessage("Erreur réseau ou serveur lors du téléversement.", "error");
        }
    });
}

// AJAX file delete with confirmation
document.querySelectorAll('form[action*="delete"]').forEach(form => {
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        if (!confirm("Supprimer ce fichier ?")) return;
        try {
            const res = await fetch(form.action, { method: 'POST' });
            let text = '';
            try {
                text = await res.text();
            } catch (err) {
                showMessage("Réponse serveur invalide.", "error");
                return;
            }
            if (res.redirected) {
                window.location.href = res.url; // For Flask redirect after delete
                return;
            }
            if (res.ok) {
                showMessage("Fichier supprimé.", "success");
                setTimeout(() => window.location.reload(), 1000);
            } else {
                showMessage(text || "Erreur lors de la suppression.", "error");
            }
        } catch (err) {
            showMessage("Erreur réseau ou serveur lors de la suppression.", "error");
        }
    });
});
