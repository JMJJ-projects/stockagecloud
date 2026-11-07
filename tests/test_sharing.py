import sqlite3
from datetime import datetime, timedelta


def share(client, file_id=1):
    return client.c.post(f'/share/{file_id}', headers={'X-CSRFToken': client.token()}).get_json()


def test_share_link_works_anonymously(app, alice):
    alice.upload(b'public')
    url = share(alice)['share_url']
    token = url.rsplit('/', 1)[1]
    alice.get('/logout')
    assert app.test_client().get(f'/shared/{token}/download').data == b'public'


def test_same_link_reused(alice):
    alice.upload()
    assert share(alice)['share_url'] == share(alice)['share_url']


def test_expired_link_refused(app, alice):
    alice.upload()
    token = share(alice)['share_url'].rsplit('/', 1)[1]
    db = sqlite3.connect(app.config['DATABASE'])
    db.execute('UPDATE share_links SET expires_at = ?', ((datetime.now() - timedelta(days=1)).isoformat(),))
    db.commit()
    assert app.test_client().get(f'/shared/{token}/download').status_code == 302


def test_deactivated_and_trashed_links_refused(app, alice):
    alice.upload()
    token = share(alice)['share_url'].rsplit('/', 1)[1]
    alice.post('/delete/1')  # trashing a file revokes its links
    assert app.test_client().get(f'/shared/{token}/download').status_code == 302


def test_download_count_only_on_download(app, alice):
    alice.upload()
    token = share(alice)['share_url'].rsplit('/', 1)[1]
    anon = app.test_client()
    anon.get(f'/shared/{token}')
    anon.get(f'/shared/{token}/download')
    count = sqlite3.connect(app.config['DATABASE']).execute(
        'SELECT download_count FROM share_links').fetchone()[0]
    assert count == 1
