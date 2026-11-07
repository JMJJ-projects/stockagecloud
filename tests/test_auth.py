def test_register_and_login(client):
    assert client.register().status_code == 302
    r = client.login()
    assert r.status_code == 302 and r.headers['Location'].endswith('/dashboard')


def test_weak_password_rejected(client):
    assert client.register(password='short').status_code == 400


def test_duplicate_username_rejected(client):
    client.register()
    assert client.register().status_code == 409


def test_wrong_password(client):
    client.register()
    assert client.login(password='Wrong1234').status_code == 401


def test_bruteforce_lockout(client):
    client.register()
    for _ in range(5):
        client.login(password='Wrong1234')
    # even the correct password is refused while locked out
    assert client.login().status_code == 429


def test_dashboard_requires_login(client):
    assert client.get('/dashboard').status_code == 302


def test_passwords_are_hashed(app, client):
    import sqlite3
    client.register()
    stored = sqlite3.connect(app.config['DATABASE']).execute('SELECT password FROM users').fetchone()[0]
    assert 'Secret123' not in stored and stored.startswith(('scrypt:', 'pbkdf2:'))
