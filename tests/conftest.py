import io
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from crypto import generate_master_key  # noqa: E402
from db import init_db  # noqa: E402

PASSWORD = 'Secret123'


@pytest.fixture
def app(tmp_path):
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test',
        'MASTER_KEY': generate_master_key(),
        'DATABASE': str(tmp_path / 'test.db'),
        'UPLOAD_FOLDER': str(tmp_path / 'uploads'),
    })
    with app.app_context():
        init_db()
    return app


class Client:
    """Thin wrapper around the Flask test client that handles CSRF tokens."""

    def __init__(self, flask_client):
        self.c = flask_client

    def token(self):
        html = self.c.get('/login').get_data(as_text=True)
        return re.search(r'name="csrf-token" content="([^"]+)"', html).group(1)

    def get(self, *a, **kw):
        return self.c.get(*a, **kw)

    def post(self, url, data=None, csrf=True, **kw):
        data = dict(data or {})
        if csrf:
            data['csrf_token'] = self.token()
        return self.c.post(url, data=data, **kw)

    def register(self, username='alice', password=PASSWORD):
        return self.post('/register', {'username': username, 'email': f'{username}@x.fr',
                                       'password': password})

    def login(self, username='alice', password=PASSWORD):
        return self.post('/login', {'username': username, 'password': password})

    def upload(self, content=b'hello world', name='notes.txt'):
        return self.post('/dashboard', {'file': (io.BytesIO(content), name)},
                         content_type='multipart/form-data')


@pytest.fixture
def client(app):
    return Client(app.test_client())


@pytest.fixture
def alice(client):
    client.register()
    client.login()
    return client


def file_rows(app, user_id=None):
    import sqlite3
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    q = 'SELECT * FROM files' + (' WHERE user_id = ?' if user_id else '')
    return db.execute(q, (user_id,) if user_id else ()).fetchall()
