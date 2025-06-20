import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash, jsonify
from db import get_db, close_db, init_db_command

# --- Flask App Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'  # Change for production!
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Register DB helpers ---
app.teardown_appcontext(close_db)
app.cli.add_command(init_db_command)

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
        try:
            db.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, password)
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
            user = db.execute(
                "SELECT * FROM users WHERE username = ? AND password = ?",
                (username, password)
            ).fetchone()
            if user:
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
                filename = file.filename
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                try:
                    file.save(filepath)
                except Exception as e:
                    flash('Erreur lors de l\'enregistrement du fichier.')
                    return redirect(url_for('dashboard'))
                try:
                    db.execute(
                        "INSERT INTO files (user_id, filename) VALUES (?, ?)",
                        (user_id, filename)
                    )
                    db.commit()
                    flash('File uploaded!')
                except Exception as e:
                    flash('Erreur lors de l\'enregistrement en base de données.')
                    if os.path.exists(filepath):
                        os.remove(filepath)
            else:
                flash('No file selected.')
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
        try:
            return send_from_directory(app.config['UPLOAD_FOLDER'], file['filename'], as_attachment=True)
        except Exception as e:
            flash('Erreur lors du téléchargement du fichier.')
            return redirect(url_for('dashboard'))
    else:
        flash('File not found or unauthorized.')
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
            flash('File deleted.')
        except Exception as e:
            flash('Erreur lors de la suppression en base de données.')
    else:
        flash('File not found or unauthorized.')
    return redirect(url_for('dashboard'))



# --- Run App ---
if __name__ == '__main__':
    app.run(debug=True)