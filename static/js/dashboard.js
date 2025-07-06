// Enhanced dashboard functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

function initializeDashboard() {
    setupFileInput();
    setupUploadForm();
    setupDeleteButtons();
    setupMessageHandling();
}

// File input enhancement with drag and drop
function setupFileInput() {
    const fileInput = document.getElementById('fileInput');
    const fileLabel = document.querySelector('.file-input-label');
    
    if (!fileInput || !fileLabel) return;

    // Update label when file is selected
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            updateFileLabel(file.name);
        }
    });

    // Drag and drop functionality
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

// Enhanced upload form handling
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

        // Show loading state
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
                // Reset form
                uploadForm.reset();
                updateFileLabel('Choisir un fichier');
                setTimeout(() => window.location.reload(), 1500);
            } else {
                showMessage(text || "Erreur lors du téléversement.", "error");
            }
        } catch (error) {
            showMessage("Erreur réseau lors du téléversement.", "error");
        } finally {
            // Restore button state
            uploadButton.innerHTML = originalText;
            uploadButton.disabled = false;
        }
    });
}

// Enhanced delete functionality
function setupDeleteButtons() {
    document.querySelectorAll('.delete-form').forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            if (!confirm("Êtes-vous sûr de vouloir supprimer ce fichier ?")) {
                return;
            }

            const deleteButton = form.querySelector('.btn-delete');
            const originalHTML = deleteButton.innerHTML;
            
            // Show loading state
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
                    // Animate card removal
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
                // Restore button state
                deleteButton.innerHTML = originalHTML;
                deleteButton.disabled = false;
            }
        });
    });
}

// Update file count display
function updateFileCount() {
    const fileCards = document.querySelectorAll('.file-card');
    const fileCountElement = document.querySelector('.file-count');
    
    if (fileCountElement) {
        const count = fileCards.length;
        fileCountElement.textContent = `${count} fichier${count > 1 ? 's' : ''}`;
        
        // Show empty state if no files
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

// Enhanced message handling
function setupMessageHandling() {
    // Auto-hide messages after 5 seconds
    const messages = document.querySelectorAll('.message');
    messages.forEach(message => {
        setTimeout(() => {
            message.style.transform = 'translateX(100%)';
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });
}

// Enhanced message display function
function showMessage(msg, type = 'info') {
    const messageContainer = document.getElementById('dashboard-message');
    if (!messageContainer) return;

    // Remove existing messages
    const existingMessages = messageContainer.querySelectorAll('.message');
    existingMessages.forEach(msg => msg.remove());

    // Create new message
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    
    const icon = type === 'success' ? 'check-circle' : 
                 type === 'error' ? 'exclamation-circle' : 'info-circle';
    
    messageDiv.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${msg}</span>
    `;

    messageContainer.appendChild(messageDiv);

    // Auto-hide after 5 seconds
    setTimeout(() => {
        messageDiv.style.transform = 'translateX(100%)';
        messageDiv.style.opacity = '0';
        setTimeout(() => messageDiv.remove(), 300);
    }, 5000);
}

// Add smooth scrolling for better UX
function smoothScrollTo(element) {
    element.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
}

// Add keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + U to focus file input
    if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
        e.preventDefault();
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.click();
        }
    }
    
    // Escape to close messages
    if (e.key === 'Escape') {
        const messages = document.querySelectorAll('.message');
        messages.forEach(message => {
            message.style.transform = 'translateX(100%)';
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 300);
        });
    }
});

// Add file size validation
function validateFileSize(file, maxSize = 50 * 1024 * 1024) { // 50MB default
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

// History
/*function formatAction(action) {
    const icons = {
        'upload': 'Téléversement',
        'download': 'Téléchargement',
        'delete': 'Suppression',
        'restore': 'Restauration',
        'permanent_delete': 'Suppression définitive'
    };
    return icons[action] || action;
}
*/

fetch('/history')
    .then(response => {
        if (!response.ok) throw new Error("Non autorisé ou erreur serveur");
        return response.json();
    })
    .then(data => {
        const tbody = document.querySelector('#historyTable tbody');
        data.forEach(entry => {
            const row = document.createElement('tr');

            row.innerHTML = `
                <td>${entry.timestamp}</td>
                <td>${entry.action}</td>
                <td>${entry.original_filename || 'N/A'}</td>
            `;
            tbody.appendChild(row);
        });
    })
    .catch(err => {
        const msg = document.getElementById('errorMessage');
        msg.textContent = err.message;
        msg.classList.remove('d-none');
    });