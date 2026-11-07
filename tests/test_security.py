import os

from conftest import file_rows


def test_post_without_csrf_token_is_rejected(client):
    r = client.post('/register', {'username': 'x', 'email': 'x@x.fr', 'password': 'Secret123'},
                    csrf=False)
    assert r.status_code == 400


def test_csrf_header_accepted_for_fetch_calls(alice):
    alice.upload()
    r = alice.c.post('/share/1', headers={'X-CSRFToken': alice.token()})
    assert r.get_json()['success'] is True


def test_security_headers(client):
    r = client.get('/mainpage')
    assert r.headers['X-Frame-Options'] == 'DENY'
    assert r.headers['X-Content-Type-Options'] == 'nosniff'
    assert "frame-ancestors 'none'" in r.headers['Content-Security-Policy']


def test_files_are_encrypted_on_disk(app, alice):
    secret = b'my bank details: 1234'
    alice.upload(secret)
    row = file_rows(app)[0]
    with open(os.path.join(app.config['UPLOAD_FOLDER'], row['filename']), 'rb') as f:
        on_disk = f.read()
    assert secret not in on_disk
    assert alice.get('/download/1').data == secret


def test_tampered_file_is_detected(app, alice):
    alice.upload(b'original content')
    path = os.path.join(app.config['UPLOAD_FOLDER'], file_rows(app)[0]['filename'])
    with open(path, 'r+b') as f:
        f.seek(20)
        f.write(b'X')
    r = alice.get('/download/1')
    assert r.status_code == 302  # redirected with an integrity error, file not served


def test_users_cannot_access_each_others_files(app, client):
    client.register('alice'); client.login('alice'); client.upload(b'alice private')
    client.get('/logout')
    client.register('bob'); client.login('bob')
    assert client.get('/download/1').status_code == 404
    client.post('/delete/1')
    assert file_rows(app)[0]['delete_date'] is None
    assert client.c.post('/share/1', headers={'X-CSRFToken': client.token()}).status_code == 404


def test_disallowed_extension(app, alice):
    alice.upload(b'#!/bin/sh', name='evil.sh')
    assert file_rows(app) == []
