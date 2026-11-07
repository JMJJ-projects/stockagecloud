import os
from datetime import datetime, timedelta

from conftest import file_rows


def test_upload_and_download(alice):
    alice.upload(b'abc', 'a.txt')
    r = alice.get('/download/1')
    assert r.data == b'abc'
    assert 'a.txt' in r.headers['Content-Disposition']


def test_trash_and_restore_keeps_file(app, alice):
    alice.upload(b'keep me')
    alice.post('/delete/1')
    assert alice.get('/download/1').status_code == 404       # not downloadable from the trash
    assert b'keep me' not in alice.get('/dashboard').data
    alice.post('/restore/1')
    assert alice.get('/download/1').data == b'keep me'        # blob survived the trip


def test_permanent_delete_removes_blob(app, alice):
    alice.upload()
    stored = file_rows(app)[0]['filename']
    alice.post('/delete/1')
    alice.post('/permanent_delete/1')
    assert file_rows(app) == []
    assert not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], stored))
    assert 'notes.txt' in alice.get('/history').get_data(as_text=True)


def test_trash_purged_after_retention(app, alice):
    import sqlite3
    alice.upload()
    alice.post('/delete/1')
    db = sqlite3.connect(app.config['DATABASE'])
    db.execute('UPDATE files SET delete_date = ?', ((datetime.now() - timedelta(days=31)).isoformat(),))
    db.commit()
    alice.get('/dashboard')
    assert file_rows(app) == []


def test_recent_trash_not_purged(app, alice):
    alice.upload()
    alice.post('/delete/1')
    alice.get('/dashboard')
    assert len(file_rows(app)) == 1


def test_quota_enforced(app, alice):
    app.config['MAX_QUOTA_BYTES'] = 10
    alice.upload(b'12345678')
    alice.upload(b'12345678')
    assert len(file_rows(app)) == 1
