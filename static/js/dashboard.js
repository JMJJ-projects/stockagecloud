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
            if (res.redirected) {
                window.location.href = res.url; // For Flask redirect after upload
                return;
            }
            const text = await res.text();
            showMessage("Fichier téléversé !", "success");
            setTimeout(() => window.location.reload(), 1000);
        } catch (err) {
            showMessage("Erreur lors du téléversement.", "error");
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
            if (res.redirected) {
                window.location.href = res.url; // For Flask redirect after delete
                return;
            }
            showMessage("Fichier supprimé.", "success");
            setTimeout(() => window.location.reload(), 1000);
        } catch (err) {
            showMessage("Erreur lors de la suppression.", "error");
        }
    });
});
