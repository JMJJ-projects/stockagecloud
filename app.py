"""StockageCloud: a small, security-focused personal cloud storage service.

Run locally:
    flask --app app init-db
    flask --app app run
"""
import hashlib
import io
import os
import secrets
import uuid
import warnings
from datetime import datetime, timedelta
from functools import wraps

from flask import (Flask, abort, flash, jsonify, redirect, render_template,
                   request, send_file, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

import crypto
import security
from db import close_db, get_db, init_db_command

ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg',
    'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'mp3', 'wav', 'flac', 'aac', 'ogg',
    'mp4', 'avi', 'mov', 'wmv', 'flv',
    'zip', 'rar', '7z', 'tar', 'gz',
}


# --------------------------------------------------------------- factory ---

def create_app(test_config=None):
    app = Flask(__name__)
    base = os.path.dirname(os.path.abspath(__file__))

    app.config.update(
        SECRET_KEY=os.environ.get('SECRET_KEY'),
        MASTER_KEY=os.environ.get('MASTER_KEY'),
        DATABASE=os.environ.get('DATABASE', os.path.join(base, 'database.db')),
        UPLOAD_FOLDER=os.environ.get('UPLOAD_FOLDER', os.path.join(base, 'uploads')),
        MAX_CONTENT_LENGTH=50 * 1024 * 1024,      # 50 MB per upload
        MAX_QUOTA_BYTES=500 * 1024 * 1024,        # 500 MB per user
        TRASH_RETENTION=timedelta(days=30),
        SHARE_LINK_DAYS=7,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.environ.get('FLASK_ENV') == 'production',
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    )
    if test_config:
        app.config.update(test_config)

    # Never fall back to a hard-coded secret: generate throwaway dev keys instead.
    if not app.config['SECRET_KEY']:
        warnings.warn('SECRET_KEY not set: using a random key (sessions reset on restart).')
        app.config['SECRET_KEY'] = secrets.token_hex(32)
    if not app.config['MASTER_KEY']:
        warnings.warn('MASTER_KEY not set: using a random key (stored files unreadable after restart).')
        app.config['MASTER_KEY'] = crypto.generate_master_key()
    app.config['MASTER_KEY_BYTES'] = crypto.load_master_key(app.config['MASTER_KEY'])

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

    @app.cli.command('gen-keys')
    def gen_keys():
        """Print fresh SECRET_KEY and MASTER_KEY values for the .env file."""
        print(f'SECRET_KEY={secrets.token_hex(32)}')
        print(f'MASTER_KEY={crypto.generate_master_key()}')
    app.before_request(security.check_csrf)
    app.after_request(security.add_security_headers)
    app.jinja_env.globals['csrf_token'] = security.get_csrf_token
    app.jinja_env.filters['dt'] = format_datetime

    register_routes(app)
    return app


# --------------------------------------------------------------- helpers ---

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped


def format_datetime(value, with_time=True):
    """Render an ISO timestamp as 07/11/2026 01:45 for the templates."""
    if not value:
        return ''
    try:
        d = datetime.fromisoformat(str(value))
    except ValueError:
        return value
    return d.strftime('%d/%m/%Y %H:%M' if with_time else '%d/%m/%Y')


def is_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def log_action(db, user_id, file_id, action, label=None):
    db.execute(
        "INSERT INTO history (user_id, file_id, file_label, action, timestamp) VALUES (?, ?, ?, ?, ?)",
        (user_id, file_id, label, action, datetime.now().isoformat()),
    )


def used_space(db, user_id):
    """Bytes used by a user. Files in the trash still count until purged."""
    row = db.execute("SELECT COALESCE(SUM(file_size), 0) AS total FROM files WHERE user_id = ?",
                     (user_id,)).fetchone()
    return row['total']


def stored_path(app, file_row):
    return os.path.join(app.config['UPLOAD_FOLDER'], file_row['filename'])


def remove_stored_file(app, file_row):
    path = stored_path(app, file_row)
    if os.path.exists(path):
        os.remove(path)


def read_decrypted(app, file_row):
    """Decrypt a stored file and verify its SHA-256 against the database."""
    with open(stored_path(app, file_row), 'rb') as f:
        blob = f.read()
    data = crypto.decrypt_file(blob, file_row['wrapped_key'],
                               app.config['MASTER_KEY_BYTES'], file_row['filename'])
    if hashlib.sha256(data).hexdigest() != file_row['file_hash']:
        raise crypto.DecryptionError('hash mismatch')
    return data


def purge_expired_trash(app, db):
    """Permanently delete files that have been in the trash longer than the retention period."""
    cutoff = (datetime.now() - app.config['TRASH_RETENTION']).isoformat()
    expired = db.execute("SELECT * FROM files WHERE delete_date IS NOT NULL AND delete_date < ?",
                         (cutoff,)).fetchall()
    for row in expired:
        try:
            remove_stored_file(app, row)
        except OSError as e:
            app.logger.error('Could not remove %s: %s', row['filename'], e)
            continue
        db.execute("DELETE FROM files WHERE id = ?", (row['id'],))
    db.commit()


def get_active_share(db, token):
    """Return (share_link, file) for a valid, unexpired token on a live file, else (None, None)."""
    link = db.execute("SELECT * FROM share_links WHERE share_token = ? AND is_active = 1",
                      (token,)).fetchone()
    if not link:
        return None, None
    if link['expires_at'] and datetime.now() > datetime.fromisoformat(link['expires_at']):
        return None, None
    file = db.execute("SELECT * FROM files WHERE id = ? AND delete_date IS NULL",
                      (link['file_id'],)).fetchone()
    return (link, file) if file else (None, None)


def send_decrypted(data, file_row):
    return send_file(io.BytesIO(data), as_attachment=True,
                     download_name=file_row['original_filename'])


# ---------------------------------------------------------------- routes ---

def register_routes(app):

    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return redirect(url_for('mainpage'))

    @app.route('/mainpage')
    def mainpage():
        return render_template('mainpage.html')

    # ---- auth --------------------------------------------------------------

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = (request.form.get('username') or '').strip()
            email = (request.form.get('email') or '').strip().lower()
            password = request.form.get('password') or ''

            if not username or not email or not password:
                flash('Tous les champs sont obligatoires.', 'error')
                return render_template('register.html'), 400
            problems = security.password_problems(password)
            if problems:
                flash('Mot de passe trop faible : ' + ', '.join(problems) + '.', 'error')
                return render_template('register.html'), 400

            db = get_db()
            try:
                db.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                           (username, email, generate_password_hash(password)))
                db.commit()
            except db.IntegrityError:
                flash("Email ou nom d'utilisateur déjà utilisé.", 'error')
                return render_template('register.html'), 409
            flash('Inscription réussie ! Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = (request.form.get('username') or '').strip()
            password = request.form.get('password') or ''
            ip = request.remote_addr or 'unknown'
            db = get_db()

            if security.is_locked_out(db, username, ip):
                flash('Trop de tentatives échouées. Réessayez dans 15 minutes.', 'error')
                return render_template('login.html'), 429

            user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if user and check_password_hash(user['password'], password):
                security.clear_failed_logins(db, username)
                session.clear()  # prevent session fixation
                session.permanent = True
                session['user_id'] = user['id']
                session['username'] = user['username']
                flash('Connexion réussie !', 'success')
                return redirect(url_for('dashboard'))

            security.record_failed_login(db, username, ip)
            flash('Identifiants invalides.', 'error')
            return render_template('login.html'), 401
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('mainpage'))

    # ---- files -------------------------------------------------------------

    @app.route('/dashboard', methods=['GET', 'POST'])
    @login_required
    def dashboard():
        db = get_db()
        user_id = session['user_id']

        if request.method == 'POST':
            file = request.files.get('file')
            if not file or not file.filename:
                flash('Aucun fichier sélectionné.', 'error')
                return redirect(url_for('dashboard'))
            if not is_allowed_file(file.filename):
                flash('Type de fichier non autorisé.', 'error')
                return redirect(url_for('dashboard'))

            data = file.read()
            used = used_space(db, user_id)
            if used + len(data) > app.config['MAX_QUOTA_BYTES']:
                flash(f"Quota dépassé : {used / 2**20:.1f} Mo utilisés sur "
                      f"{app.config['MAX_QUOTA_BYTES'] // 2**20} Mo.", 'error')
                return redirect(url_for('dashboard'))

            original = secure_filename(file.filename) or 'fichier'
            stored_name = str(uuid.uuid4())  # no extension: nothing on disk is directly servable
            blob, wrapped = crypto.encrypt_file(data, app.config['MASTER_KEY_BYTES'], stored_name)
            path = os.path.join(app.config['UPLOAD_FOLDER'], stored_name)
            with open(path, 'wb') as f:
                f.write(blob)

            try:
                cur = db.execute(
                    "INSERT INTO files (user_id, filename, original_filename, file_hash, file_size,"
                    " wrapped_key, upload_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (user_id, stored_name, original, hashlib.sha256(data).hexdigest(), len(data),
                     wrapped, datetime.now().isoformat()))
                log_action(db, user_id, cur.lastrowid, 'upload', original)
                db.commit()
            except Exception:
                db.rollback()
                os.remove(path)
                raise
            flash('Fichier téléversé avec succès !', 'success')
            return redirect(url_for('dashboard'))

        purge_expired_trash(app, db)
        files = db.execute("SELECT * FROM files WHERE user_id = ? AND delete_date IS NULL "
                           "ORDER BY upload_date DESC", (user_id,)).fetchall()
        return render_template('dashboard.html', files=files, username=session['username'],
                               used_space=used_space(db, user_id),
                               max_quota=app.config['MAX_QUOTA_BYTES'])

    @app.route('/download/<int:file_id>')
    @login_required
    def download(file_id):
        db = get_db()
        file = db.execute("SELECT * FROM files WHERE id = ? AND user_id = ? AND delete_date IS NULL",
                          (file_id, session['user_id'])).fetchone()
        if not file:
            abort(404)
        try:
            data = read_decrypted(app, file)
        except (OSError, crypto.DecryptionError):
            app.logger.error('Integrity check failed for file %s', file_id)
            flash('Erreur : le fichier est corrompu ou a été altéré.', 'error')
            return redirect(url_for('dashboard'))
        log_action(db, session['user_id'], file_id, 'download', file['original_filename'])
        db.commit()
        return send_decrypted(data, file)

    @app.route('/delete/<int:file_id>', methods=['POST'])
    @login_required
    def delete(file_id):
        """Move a file to the trash. The encrypted blob is kept so it can be restored."""
        db = get_db()
        cur = db.execute("UPDATE files SET delete_date = ? WHERE id = ? AND user_id = ? "
                         "AND delete_date IS NULL",
                         (datetime.now().isoformat(), file_id, session['user_id']))
        if cur.rowcount:
            db.execute("UPDATE share_links SET is_active = 0 WHERE file_id = ?", (file_id,))
            log_action(db, session['user_id'], file_id, 'delete')
            db.commit()
            flash('Fichier déplacé dans la corbeille.', 'success')
        else:
            flash('Fichier introuvable ou non autorisé.', 'error')
        return redirect(url_for('dashboard'))

    @app.route('/trash')
    @login_required
    def trash():
        deleted_files = get_db().execute(
            "SELECT * FROM files WHERE user_id = ? AND delete_date IS NOT NULL "
            "ORDER BY delete_date DESC", (session['user_id'],)).fetchall()
        return render_template('trash.html', deleted_files=deleted_files,
                               username=session['username'],
                               retention_days=app.config['TRASH_RETENTION'].days)

    @app.route('/restore/<int:file_id>', methods=['POST'])
    @login_required
    def restore(file_id):
        db = get_db()
        cur = db.execute("UPDATE files SET delete_date = NULL WHERE id = ? AND user_id = ? "
                         "AND delete_date IS NOT NULL", (file_id, session['user_id']))
        if cur.rowcount:
            log_action(db, session['user_id'], file_id, 'restore')
            db.commit()
            flash('Fichier restauré avec succès.', 'success')
        else:
            flash('Fichier introuvable ou non autorisé.', 'error')
        return redirect(url_for('trash'))

    @app.route('/permanent_delete/<int:file_id>', methods=['POST'])
    @login_required
    def permanent_delete(file_id):
        db = get_db()
        file = db.execute("SELECT * FROM files WHERE id = ? AND user_id = ? "
                          "AND delete_date IS NOT NULL",
                          (file_id, session['user_id'])).fetchone()
        if not file:
            flash('Fichier introuvable ou non autorisé.', 'error')
            return redirect(url_for('trash'))
        remove_stored_file(app, file)
        db.execute("UPDATE history SET file_label = COALESCE(file_label, ?) WHERE file_id = ?",
                   (file['original_filename'], file_id))
        db.execute("DELETE FROM files WHERE id = ?", (file_id,))
        log_action(db, session['user_id'], None, 'permanent_delete', file['original_filename'])
        db.commit()
        flash('Fichier supprimé définitivement.', 'success')
        return redirect(url_for('trash'))

    @app.route('/history')
    @login_required
    def history():
        entries = get_db().execute("""
            SELECT h.*, COALESCE(f.original_filename, h.file_label) AS original_filename
            FROM history h LEFT JOIN files f ON h.file_id = f.id
            WHERE h.user_id = ? ORDER BY h.id DESC LIMIT 50
        """, (session['user_id'],)).fetchall()
        return render_template('history.html', history_entries=entries,
                               username=session['username'])

    # ---- sharing -----------------------------------------------------------

    @app.route('/share/<int:file_id>', methods=['POST'])
    @login_required
    def share_file(file_id):
        db = get_db()
        file = db.execute("SELECT * FROM files WHERE id = ? AND user_id = ? AND delete_date IS NULL",
                          (file_id, session['user_id'])).fetchone()
        if not file:
            return jsonify(success=False, message='Fichier introuvable ou non autorisé.'), 404

        existing = db.execute("SELECT * FROM share_links WHERE file_id = ? AND is_active = 1 "
                              "AND (expires_at IS NULL OR expires_at > ?)",
                              (file_id, datetime.now().isoformat())).fetchone()
        if existing:
            token, message = existing['share_token'], 'Lien de partage existant récupéré.'
        else:
            token = secrets.token_urlsafe(32)
            now = datetime.now()
            db.execute("INSERT INTO share_links (file_id, share_token, created_by, created_at,"
                       " expires_at) VALUES (?, ?, ?, ?, ?)",
                       (file_id, token, session['user_id'], now.isoformat(),
                        (now + timedelta(days=app.config['SHARE_LINK_DAYS'])).isoformat()))
            log_action(db, session['user_id'], file_id, 'share', file['original_filename'])
            db.commit()
            message = 'Lien de partage créé avec succès !'
        return jsonify(success=True, message=message,
                       share_url=url_for('shared_file', token=token, _external=True))

    @app.route('/shared/<token>')
    def shared_file(token):
        link, file = get_active_share(get_db(), token)
        if not link:
            flash('Lien de partage invalide ou expiré.', 'error')
            return redirect(url_for('mainpage'))
        return render_template('shared_file.html', file=file, share_link=link)

    @app.route('/shared/<token>/download')
    def download_shared_file(token):
        db = get_db()
        link, file = get_active_share(db, token)
        if not link:
            flash('Lien de partage invalide ou expiré.', 'error')
            return redirect(url_for('mainpage'))
        try:
            data = read_decrypted(app, file)
        except (OSError, crypto.DecryptionError):
            flash('Erreur : le fichier est corrompu ou a été altéré.', 'error')
            return redirect(url_for('shared_file', token=token))
        db.execute("UPDATE share_links SET download_count = download_count + 1 WHERE id = ?",
                   (link['id'],))
        db.commit()
        return send_decrypted(data, file)

    @app.route('/manage_shares')
    @login_required
    def manage_shares():
        links = get_db().execute("""
            SELECT sl.*, f.original_filename, f.file_size, f.upload_date
            FROM share_links sl JOIN files f ON sl.file_id = f.id
            WHERE sl.created_by = ? AND sl.is_active = 1 AND f.delete_date IS NULL
            ORDER BY sl.created_at DESC
        """, (session['user_id'],)).fetchall()
        return render_template('manage_shares.html', share_links=links,
                               username=session['username'])

    @app.route('/deactivate_share/<int:share_id>', methods=['POST'])
    @login_required
    def deactivate_share(share_id):
        db = get_db()
        cur = db.execute("UPDATE share_links SET is_active = 0 WHERE id = ? AND created_by = ?",
                         (share_id, session['user_id']))
        db.commit()
        if cur.rowcount:
            flash('Lien de partage désactivé avec succès.', 'success')
        else:
            flash('Lien de partage introuvable ou non autorisé.', 'error')
        return redirect(url_for('manage_shares'))

    @app.errorhandler(413)
    def too_large(_e):
        flash('Fichier trop volumineux (50 Mo maximum).', 'error')
        return redirect(url_for('dashboard'))


app = create_app()

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')
