from flask import url_for

def test_index(client):
    r = client.get('/')
    assert r.status_code == 200
    assert 'Welcome' in r.unicode_body

def test_signup_missing_username(client):
    r = client.get('/signup/')
    assert r.form.method == 'post'

    r.form.set('username', '')
    r.form.set('password', 'p/q2-q4!')
    r.form.set('email', 'frodo@marksth.fun')
    r = r.form.submit()
    assert r.status_code == 302

    r = r.follow()
    assert 'username is empty' in r.unicode_body

    # Fun fact: Ken Thompson's Unix password was finally disclosed.
    # It's `p/q2-q4!`, which is a notation in chess to move pawn
    # from Queen's 2 to Queen's 4.
    # <https://leahneukirchen.org/blog/archive/2019/10/ken-thompson-s-unix-password.html>

def test_signup_missing_password(client):
    r = client.get('/signup/')
    assert r.form.method == 'post'

    r.form.set('username', 'frodo')
    r.form.set('password', '')
    r.form.set('email', 'frodo@marksth.fun')
    r = r.form.submit()
    assert r.status_code == 302

    r = r.follow()
    assert 'password is empty' in r.unicode_body

def test_signup_missing_email(client):
    r = client.get('/signup/')
    assert r.form.method == 'post'

    r.form.set('username', 'frodo')
    r.form.set('password', 'p/q2-q4!')
    r.form.set('email', '')
    r = r.form.submit()
    assert r.status_code == 302

    r = r.follow()
    assert 'email is empty' in r.unicode_body

def signup_fresh_user(client, user='frodo', password='p/q2-q4!', email='frodo@marksth.fun'):
    r = client.get('/signup/')
    r.form.set('username', 'frodo')
    r.form.set('password', 'p/q2-q4!')
    r.form.set('email', 'frodo@marksth.fun')
    r.form.submit()
    return r.follow()

def test_signup_uncharged_user(client):
    # Given a new user (uncharged)
    signup_fresh_user(client, 'frodo', 'p/q2-q4!', 'frodo@marksth.fun')

    #   and he lands on signup page
    r = client.get('/signup/')
    assert r.form.method == 'post'

    # When he submits the form
    r.form.set('username', 'frodo')
    r.form.set('password', 'p/q1-q4!')
    r.form.set('email', 'sam@marksth.fun')
    r = r.form.submit()

    # Then he should be able to refresh all data.
    assert r.status_code == 302
    r = r.follow()
    assert r.request.path == '/signup/confirm/'

def test_signup_fresh_user(client):
    r = client.get('/signup/')
    assert r.form.method == 'post'

    # When he submits the form
    r.form.set('username', 'frodo')
    r.form.set('password', 'p/q2-q4!')
    r.form.set('email', 'frodo@marksth.fun')
    r = r.form.submit()

    # Then he should be able to refresh all data.
    assert r.status_code == 302
    r = r.follow()
    assert r.request.path == '/signup/confirm/'


def test_confirm_signup(client):
    r = signup_fresh_user(client, 'frodo', 'p/q2-q4!', 'frodo@marksth.fun')

