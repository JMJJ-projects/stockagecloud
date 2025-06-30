import sqlite3
from flask import g, current_app
import click

def get_db():
    try:
        if 'db' not in g:
            g.db = sqlite3.connect('database.db')
            g.db.row_factory = sqlite3.Row
        return g.db
    except Exception as e:
        # Optionally log the error here
        raise RuntimeError('Erreur lors de la connexion à la base de données.')

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    try:
        db = get_db()
        with current_app.open_resource('schema.sql') as f:
            db.executescript(f.read().decode('utf8'))
    except Exception as e:
        # Optionally log the error here
        raise RuntimeError('Erreur lors de l\'initialisation de la base de données.')

@click.command('init-db')
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')