// JS principal pour l'app
console.log('App chargé');

document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData();
    const fileInput = this.file;
    if (!fileInput.files.length) return;
    formData.append('file', fileInput.files[0]);
    const res = await fetch('/upload', {
        method: 'POST',
        body: formData
    });
    const data = await res.json();
    const resultDiv = document.getElementById('uploadResult');
    if (res.ok) {
        resultDiv.textContent = 'Fichier uploadé avec succès !';
        fetchFiles();
    } else {
        resultDiv.textContent = data.error || 'Erreur lors de l\'upload';
    }
});

async function fetchFiles() {
    const res = await fetch('/files');
    const files = await res.json();
    const appDiv = document.getElementById('app');
    if (files.length === 0) {
        appDiv.innerHTML = '<p>Aucun fichier uploadé.</p>';
        return;
    }
    let html = '<h2>Mes fichiers</h2><ul>';
    for (const file of files) {
        html += `<li>${file.filename} <small>(${file.uploaded_at})</small> ` +
            `<button onclick="downloadFile(${file.id})">Télécharger</button> ` +
            `<button onclick="deleteFile(${file.id})">Supprimer</button></li>`;
    }
    html += '</ul>';
    appDiv.innerHTML = html;
}

window.downloadFile = async function(fileId) {
    const res = await fetch(`/download/${fileId}`);
    const data = await res.json();
    if (res.ok && data.url) {
        window.open(data.url, '_blank');
    } else {
        alert(data.error || 'Erreur lors du téléchargement');
    }
}

window.deleteFile = async function(fileId) {
    if (!confirm('Supprimer ce fichier ?')) return;
    const res = await fetch(`/delete/${fileId}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok) {
        fetchFiles();
    } else {
        alert(data.error || 'Erreur lors de la suppression');
    }
}

fetchFiles(); 