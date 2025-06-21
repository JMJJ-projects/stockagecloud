import os
import uuid
import hashlib
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from db import get_db, close_db, init_db_command

# --- Flask App Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'  # Change for production!
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

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
    if request.method == 'POST' and request.is_json:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        if not username or not email or not password:
            return jsonify({'error': 'Tous les champs sont obligatoires.'}), 400
        
        # Hash the password before storing
        hashed_password = generate_password_hash(password)
        
        try:
            db.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, hashed_password)
            )
            db.commit()
            return jsonify({'success': True}), 200
        except db.IntegrityError:
            return jsonify({'error': 'Email ou nom d\'utilisateur déjà utilisé.'}), 400
        except Exception as e:
            return jsonify({'error': "Erreur inattendue l'inscription."}), 500
    return render_template('register.html')


# --- Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    db = get_db()
    if request.method == 'POST' and request.is_json:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
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
                return jsonify({'success': True}), 200
            else:
                return jsonify({'error': 'Identifiants invalides.'}), 401
        except Exception as e:
            return jsonify({'error': "Erreur inattendue lors de la connexion."}), 500
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

    if request.method == 'POST':
        try:
            file = request.files['file']
            if file and file.filename:
                # Check file type
                if not is_allowed_file(file.filename):
                    flash('Type de fichier non autorisé.')
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
                    flash('Erreur lors de l\'enregistrement du fichier.')
                    return redirect(url_for('dashboard'))
                
                try:
                    db.execute(
                        "INSERT INTO files (user_id, filename, original_filename, file_hash, file_size, upload_date) VALUES (?, ?, ?, ?, ?, ?)",
                        (user_id, unique_filename, safe_original_name, file_hash, file_size, datetime.now().isoformat())
                    )
                    db.commit()
                    flash('Fichier téléversé avec succès!')
                except Exception as e:
                    flash('Erreur lors de l\'enregistrement en base de données.')
                    if os.path.exists(filepath):
                        os.remove(filepath)
            else:
                flash('Aucun fichier sélectionné.')
        except Exception as e:
            flash('Erreur inattendue lors du téléversement.')

    try:
        files = db.execute(
            "SELECT * FROM files WHERE user_id = ? ORDER BY upload_date DESC",
            (user_id,)
        ).fetchall()
    except Exception as e:
        flash('Erreur lors de la récupération des fichiers.')
        files = []
    return render_template('dashboard.html', files=files, username=session['username'])

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
        flash('Erreur lors de la récupération du fichier.')
        return redirect(url_for('dashboard'))
    
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file['filename'])
        if os.path.exists(filepath):
            try:
                # Verify file integrity
                current_hash = get_file_hash(filepath)
                if current_hash != file['file_hash']:
                    flash('Erreur: Le fichier a été corrompu.')
                    return redirect(url_for('dashboard'))
                
                # Serve file with original filename
                return send_from_directory(
                    app.config['UPLOAD_FOLDER'], 
                    file['filename'], 
                    as_attachment=True,
                    download_name=file['original_filename']
                )
            except Exception as e:
                flash('Erreur lors du téléchargement du fichier.')
                return redirect(url_for('dashboard'))
        else:
            flash('Fichier introuvable sur le serveur.')
            return redirect(url_for('dashboard'))
    else:
        flash('Fichier introuvable ou non autorisé.')
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
        flash('Erreur lors de la récupération du fichier à supprimer.')
        return redirect(url_for('dashboard'))
    
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file['filename'])
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            flash('Erreur lors de la suppression du fichier sur le disque.')
            return redirect(url_for('dashboard'))
        try:
            db.execute("DELETE FROM files WHERE id = ?", (file_id,))
            db.commit()
            flash('Fichier supprimé avec succès.')
        except Exception as e:
            flash('Erreur lors de la suppression en base de données.')
    else:
        flash('Fichier introuvable ou non autorisé.')
    return redirect(url_for('dashboard'))



# --- Run App ---
if __name__ == '__main__':
    app.run(debug=True)