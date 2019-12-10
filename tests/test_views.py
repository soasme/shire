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
    r.form.set('password', 'P/q2-q4!')
    r.form.set('email', 'frodo@marksth.fun')
    r = r.form.submit()

    # Then he should be able to refresh all data.
    assert r.status_code == 302
    r = r.follow()
    assert r.request.path == '/'

    # <https://leahneukirchen.org/blog/archive/2019/10/ken-thompson-s-unix-password.html>
