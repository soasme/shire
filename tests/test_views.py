from flask import url_for


def test_index(client):
    r = client.get('/')
    assert r.status_code == 200
    assert 'Welcome' in r.unicode_body

def test_signup_fresh_user(client):
    r = client.get('/user/register/')
    assert r.form.method == 'POST'

    # When he submits the form
    r.form.set('username', 'frodo')
    # <https://leahneukirchen.org/blog/archive/2019/10/ken-thompson-s-unix-password.html>
    r.form.set('password', 'P/q2-q4!')
    r.form.set('email', 'frodo@marksth.fun')
    r = r.form.submit()

    # Then he should be able to refresh all data.
    assert r.status_code == 302
    r = r.follow()
    assert r.request.path == '/'

    # Then he will be an active user if clicking the registration link.
    from shire.models import User
    user = client.app.user_manager.find_user_by_username('frodo')
    r = client.get(client.app.user_manager.get_registration_link(user, external=False))
    assert r.status_code == 302
    r = r.follow()
    assert r.request.path == '/'

    r = client.get('/user/login/')
    r.form.set('username', 'frodo')
    r.form.set('password', 'P/q2-q4!')
    r = r.form.submit()
    r = r.follow()
    assert '/account/' in r.unicode_body
