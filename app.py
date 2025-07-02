import os
import uuid
import hashlib
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from db import get_db, close_db, init_db_command

# --- Flask App Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'  # Change for production!
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
MAX_QUOTA_BYTES = 500 * 1024 * 1024 #500 Mo

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Register DB helpers ---
app.teardown_appcontext(close_db)
app.cli.add_command(init_db_command)

# --- File Security Functions ---
def generate_unique_filename(original_filename):
    """Generate a unique filename using UUID and preserve original extension."""
    # Sanitize the original filename
    safe_filename = secure_filename(original_filename)
    
    # Get file extension
    _, file_extension = os.path.splitext(safe_filename)
    
    # Generate unique identifier
    unique_id = str(uuid.uuid4())
    
    # Combine unique ID with original extension
    unique_filename = f"{unique_id}{file_extension}"
    
    return unique_filename, safe_filename

def get_file_hash(file_path):
    """Calculate SHA-256 hash of a file."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def is_allowed_file(filename):
    """Check if file type is allowed."""
    ALLOWED_EXTENSIONS = {
        'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg',
        'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
        'mp3', 'wav', 'flac', 'aac', 'ogg',
        'mp4', 'avi', 'mov', 'wmv', 'flv',
        'zip', 'rar', '7z', 'tar', 'gz'
    }
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Routes ---

@app.route('/')
def index():    
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('mainpage'))

# --- Main Page ---
@app.route('/mainpage')
def mainpage():
    return render_template('mainpage.html')

# --- Registration ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    db = get_db()
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not username or not email or not password:
            flash('Tous les champs sont obligatoires.', 'error')
            return render_template('register.html')
        
        # Hash the password before storing
        hashed_password = generate_password_hash(password)
        
        try:
            db.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, hashed_password)
            )
            db.commit()
            flash('Inscription réussie! Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('login'))
        except db.IntegrityError:
            flash('Email ou nom d\'utilisateur déjà utilisé.', 'error')
            return render_template('register.html')
        except Exception as e:
            flash("Erreur inattendue lors de l'inscription.", 'error')
            return render_template('register.html')
    
    return render_template('register.html')


# --- Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    db = get_db()
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Nom d\'utilisateur et mot de passe requis.', 'error')
            return render_template('login.html')
        
        try:
            # First, get the user by username only
            user = db.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            ).fetchone()
            
            # Then verify the password
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                flash('Connexion réussie!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Identifiants invalides.', 'error')
                return render_template('login.html')
        except Exception as e:
            flash("Erreur inattendue lors de la connexion.", 'error')
            return render_template('login.html')
    
    return render_template('login.html')

# --- Logout ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('mainpage'))

# --- Dashboard (File List & Upload) ---
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    user_id = session['user_id']


    #calcule de l'espace utilisé
    result = db.execute("SELECT SUM(file_size) AS total FROM files WHERE user_id = ? AND delete_data = 'NULL'",(user_id,)).fetchone()
    used_space = result["total"] if result["total"] else 0


    if request.method == 'POST':
        try:
            file = request.files['file']
            if file and file.filename:
                #check quota
                file.seek(0, os.SEEK_END)
                file_size_new = file.tell()
                file.seek(0)

                if used_space + file_size_new > MAX_QUOTA_BYTES:
                    flash(f"Quota dépassé : vous avez utilisé {round(used_space / (1024*1024),1)} Mo sur 500 Mo. Veuillez supprimer des fichiers avant de téléverser.", "error")
                    return redirect(url_for('dashboard')))
                # Check file type
                if not is_allowed_file(file.filename):
                    flash('Type de fichier non autorisé.', 'error')
                    return redirect(url_for('dashboard'))
                
                # Generate unique filename and sanitize original name
                unique_filename, safe_original_name = generate_unique_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                
                try:
                    file.save(filepath)
                    
                    # Calculate file hash
                    file_hash = get_file_hash(filepath)
                    
                    # Get file size
                    file_size = os.path.getsize(filepath)
                    
                except Exception as e:
                    flash('Erreur lors de l\'enregistrement du fichier.', 'error')
                    return redirect(url_for('dashboard'))
                
                try:
                    db.execute(
                        "INSERT INTO files (user_id, filename, original_filename, file_hash, file_size, upload_date, delete_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (user_id, unique_filename, safe_original_name, file_hash, file_size, datetime.now().isoformat(), 'NULL')
                    )
                    db.commit()
                    flash('Fichier téléversé avec succès!', 'success')
                except Exception as e:
                    flash('Erreur lors de l\'enregistrement en base de données.', 'error')
                    if os.path.exists(filepath):
                        os.remove(filepath)
            else:
                flash('Aucun fichier sélectionné.', 'error')
        except Exception as e:
            flash('Erreur inattendue lors du téléversement.', 'error')


    try:
        # Calculer la date limite (30 secondes avant maintenant)
        cutoff_date = datetime.now() - timedelta(seconds=30)
        
        # Récupérer les fichiers à supprimer
        old_files = db.execute(
            "SELECT * FROM files WHERE delete_date != 'NULL' AND delete_date < ?",
            (cutoff_date.isoformat(),)
        ).fetchall()
        
        # Supprimer chaque fichier
        for file in old_files:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file['filename'])
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as e:
                    app.logger.error(f"Erreur suppression fichier {filepath}: {e}")
                    continue
            
            # Supprimer l'entrée en base
            db.execute("DELETE FROM files WHERE id = ?", (file['id'],))
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        app.logger.error(f"Erreur nettoyage corbeille: {e}")




    try:
        files = db.execute(
            "SELECT * FROM files WHERE user_id = ? AND delete_date = 'NULL' ORDER BY upload_date DESC",
            (user_id,)
        ).fetchall()
    except Exception as e:
        flash('Erreur lors de la récupération des fichiers.', 'error')
        files = []
    return render_template('dashboard.html', files=files, username=session['username'], used_space=used_space, max_quota=MAX_QUOTA_BYTES))

# --- Download File ---
@app.route('/download/<int:file_id>')
def download(file_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    try:
        file = db.execute(
            "SELECT * FROM files WHERE id = ? AND user_id = ?",
            (file_id, session['user_id'])
        ).fetchone()
    except Exception as e:
        flash('Erreur lors de la récupération du fichier.', 'error')
        return redirect(url_for('dashboard'))
    
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file['filename'])
        if os.path.exists(filepath):
            try:
                # Verify file integrity
                current_hash = get_file_hash(filepath)
                if current_hash != file['file_hash']:
                    flash('Erreur: Le fichier a été corrompu.', 'error')
                    return redirect(url_for('dashboard'))
                
                # Serve file with original filename
                return send_from_directory(
                    app.config['UPLOAD_FOLDER'], 
                    file['filename'], 
                    as_attachment=True,
                    download_name=file['original_filename']
                )
            except Exception as e:
                flash('Erreur lors du téléchargement du fichier.', 'error')
                return redirect(url_for('dashboard'))
        else:
            flash('Fichier introuvable sur le serveur.', 'error')
            return redirect(url_for('dashboard'))
    else:
        flash('Fichier introuvable ou non autorisé.', 'error')
        return redirect(url_for('dashboard'))

# --- Delete File ---
@app.route('/delete/<int:file_id>', methods=['POST'])
def delete(file_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    try:
        file = db.execute(
            "SELECT * FROM files WHERE id = ? AND user_id = ?",
            (file_id, session['user_id'])
        ).fetchone()
    except Exception as e:
        flash('Erreur lors de la récupération du fichier à supprimer.', 'error')
        return redirect(url_for('dashboard'))
    
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file['filename'])
        try:
            db.execute("UPDATE files SET delete_date = ? WHERE id = ? AND user_id = ?", (datetime.now().isoformat(), file_id, session['user_id']))

            db.commit()
            flash('Fichier supprimé avec succès.', 'success')
        except Exception as e:
            flash('Erreur lors de la suppression en base de données.', 'error')
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            flash('Erreur lors de la suppression du fichier sur le disque.', 'error')
            return redirect(url_for('dashboard'))
    else:
        flash('Fichier introuvable ou non autorisé.', 'error')
    return redirect(url_for('dashboard'))

# --- Trash Page ---
@app.route('/trash')
def trash():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    try:
        # Récupérer les fichiers supprimés (avec delete_date non NULL)
        deleted_files = db.execute(
            "SELECT * FROM files WHERE user_id = ? AND delete_date != 'NULL' ORDER BY delete_date DESC",
            (session['user_id'],)
        ).fetchall()
    except Exception as e:
        flash('Erreur lors de la récupération des fichiers supprimés.', 'error')
        deleted_files = []
    
    return render_template('trash.html', deleted_files=deleted_files, username=session['username'])

# --- Restore File ---
@app.route('/restore/<int:file_id>', methods=['POST'])
def restore(file_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    try:
        # Vérifier que le fichier appartient bien à l'utilisateur
        file = db.execute(
            "SELECT * FROM files WHERE id = ? AND user_id = ? AND delete_date != 'NULL'",
            (file_id, session['user_id'])
        ).fetchone()
        
        if file:
            # Restaurer le fichier (mettre delete_date à NULL)
            db.execute(
                "UPDATE files SET delete_date = 'NULL' WHERE id = ?",
                (file_id,)
            )
            db.commit()
            flash('Fichier restauré avec succès.', 'success')
        else:
            flash('Fichier introuvable ou non autorisé.', 'error')
    except Exception as e:
        flash('Erreur lors de la restauration du fichier.', 'error')
    
    return redirect(url_for('trash'))

# --- Permanent Delete ---
@app.route('/permanent_delete/<int:file_id>', methods=['POST'])
def permanent_delete(file_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    try:
        # Vérifier que le fichier appartient bien à l'utilisateur
        file = db.execute(
            "SELECT * FROM files WHERE id = ? AND user_id = ? AND delete_date != 'NULL'",
            (file_id, session['user_id'])
        ).fetchone()
        
        if file:
            # Supprimer physiquement le fichier
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file['filename'])
            if os.path.exists(filepath):
                os.remove(filepath)
            
            # Supprimer l'entrée en base de données
            db.execute("DELETE FROM files WHERE id = ?", (file_id,))
            db.commit()
            flash('Fichier supprimé définitivement.', 'success')
        else:
            flash('Fichier introuvable ou non autorisé.', 'error')
    except Exception as e:
        flash('Erreur lors de la suppression définitive.', 'error')
    
    return redirect(url_for('trash'))

# --- Run App ---
if __name__ == '__main__':
    app.run(debug=True)