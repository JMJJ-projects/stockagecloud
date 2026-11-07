document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

function initializeDashboard() {
    setupFileInput();
    setupUploadForm();
    setupDeleteButtons();
    setupMessageHandling();
    setupShareButtons();
}

function setupFileInput() {
    const fileInput = document.getElementById('fileInput');
    const fileLabel = document.querySelector('.file-input-label');
    
    if (!fileInput || !fileLabel) return;

    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            updateFileLabel(file.name);
        }
    });

    fileLabel.addEventListener('dragover', function(e) {
        e.preventDefault();
        fileLabel.style.borderColor = '#1a73e8';
        fileLabel.style.background = '#f0f7ff';
    });

    fileLabel.addEventListener('dragleave', function(e) {
        e.preventDefault();
        fileLabel.style.borderColor = '#cbd5e1';
        fileLabel.style.background = '#f8fafc';
    });

    fileLabel.addEventListener('drop', function(e) {
        e.preventDefault();
        fileLabel.style.borderColor = '#cbd5e1';
        fileLabel.style.background = '#f8fafc';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            updateFileLabel(files[0].name);
        }
    });
}

function updateFileLabel(fileName) {
    const fileLabel = document.querySelector('.file-input-label');
    if (!fileLabel) return;
    
    const span = fileLabel.querySelector('span');
    const small = fileLabel.querySelector('small');
    
    if (span && small) {
        span.textContent = fileName;
        small.textContent = 'Cliquez pour changer de fichier';
    }
}

function setupUploadForm() {
    const uploadForm = document.querySelector('.upload-form');
    if (!uploadForm) return;

    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const fileInput = uploadForm.querySelector('input[type="file"]');
        const uploadButton = uploadForm.querySelector('.btn-upload');
        
        if (!fileInput.files.length) {
            showMessage("Veuillez sélectionner un fichier.", "error");
            return;
        }

        const originalText = uploadButton.innerHTML;
        uploadButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Téléversement...';
        uploadButton.disabled = true;

        const formData = new FormData(uploadForm);
        
        try {
            const response = await fetch(uploadForm.action, {
                method: 'POST',
                body: formData
            });

            if (response.redirected) {
                window.location.href = response.url;
                return;
            }

            const text = await response.text();
            
            if (response.ok) {
                showMessage("Fichier téléversé avec succès !", "success");
                uploadForm.reset();
                updateFileLabel('Choisir un fichier');
                setTimeout(() => window.location.reload(), 1500);
            } else {
                showMessage(text || "Erreur lors du téléversement.", "error");
            }
        } catch (error) {
            showMessage("Erreur réseau lors du téléversement.", "error");
        } finally {
            uploadButton.innerHTML = originalText;
            uploadButton.disabled = false;
        }
    });
}

function setupDeleteButtons() {
    document.querySelectorAll('.delete-form').forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            if (!confirm("Êtes-vous sûr de vouloir supprimer ce fichier ?")) {
                return;
            }

            const deleteButton = form.querySelector('.btn-delete');
            const originalHTML = deleteButton.innerHTML;
            
            deleteButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            deleteButton.disabled = true;

            try {
                const response = await fetch(form.action, { 
                    method: 'POST' 
                });

                if (response.redirected) {
                    window.location.href = response.url;
                    return;
                }

                const text = await response.text();
                
                if (response.ok) {
                    showMessage("Fichier supprimé avec succès.", "success");
                    const fileCard = form.closest('.file-card');
                    if (fileCard) {
                        fileCard.style.transform = 'scale(0.8)';
                        fileCard.style.opacity = '0';
                        setTimeout(() => {
                            fileCard.remove();
                            updateFileCount();
                        }, 300);
                    } else {
                        setTimeout(() => window.location.reload(), 1500);
                    }
                } else {
                    showMessage(text || "Erreur lors de la suppression.", "error");
                }
            } catch (error) {
                showMessage("Erreur réseau lors de la suppression.", "error");
            } finally {
                deleteButton.innerHTML = originalHTML;
                deleteButton.disabled = false;
            }
        });
    });
}

function updateFileCount() {
    const fileCards = document.querySelectorAll('.file-card');
    const fileCountElement = document.querySelector('.file-count');
    
    if (fileCountElement) {
        const count = fileCards.length;
        fileCountElement.textContent = `${count} fichier${count > 1 ? 's' : ''}`;
        
        if (count === 0) {
            const filesSection = document.querySelector('.files-section');
            const filesGrid = document.querySelector('.files-grid');
            
            if (filesGrid) {
                filesGrid.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-folder-open"></i>
                        <h3>Aucun fichier</h3>
                        <p>Vous n'avez pas encore téléversé de fichiers.</p>
                    </div>
                `;
            }
        }
    }
}

function setupMessageHandling() {
    const messages = document.querySelectorAll('.message');
    messages.forEach(message => {
        setTimeout(() => {
            message.style.transform = 'translateX(100%)';
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });
}

function showMessage(msg, type = 'info') {
    const messageContainer = document.getElementById('dashboard-message');
    if (!messageContainer) return;
    const existingMessages = messageContainer.querySelectorAll('.message');
    existingMessages.forEach(msg => msg.remove());

    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    
    const icon = type === 'success' ? 'check-circle' : 
                 type === 'error' ? 'exclamation-circle' : 'info-circle';
    
    messageDiv.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${msg}</span>
    `;

    messageContainer.appendChild(messageDiv);

    setTimeout(() => {
        messageDiv.style.transform = 'translateX(100%)';
        messageDiv.style.opacity = '0';
        setTimeout(() => messageDiv.remove(), 300);
    }, 5000);
}

function smoothScrollTo(element) {
    element.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
}

document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
        e.preventDefault();
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.click();
        }
    }
    if (e.key === 'Escape') {
        const messages = document.querySelectorAll('.message');
        messages.forEach(message => {
            message.style.transform = 'translateX(100%)';
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 300);
        });
    }
});

function validateFileSize(file, maxSize = 50 * 1024 * 1024) {
    if (file.size > maxSize) {
        showMessage(`Le fichier est trop volumineux. Taille maximale: ${formatFileSize(maxSize)}`, "error");
        return false;
    }
    return true;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}


function setupShareButtons() {
}

function shareFile(fileId) {
    const shareButton = event.target.closest('.btn-share');
    const originalHTML = shareButton.innerHTML;
    shareButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    shareButton.disabled = true;

    fetch(`/share/${fileId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            navigator.clipboard.writeText(data.share_url).then(() => {
                showMessage('Lien de partage copié dans le presse-papiers !', 'success');
            }).catch(() => {
                prompt('Lien de partage créé. Copiez ce lien:', data.share_url);
            });
        } else {
            showMessage(data.message || 'Erreur lors de la création du lien de partage.', 'error');
        }
    })
    .catch(error => {
        showMessage('Erreur réseau lors de la création du lien de partage.', 'error');
    })
    .finally(() => {
        shareButton.innerHTML = originalHTML;
        shareButton.disabled = false;
    });
}