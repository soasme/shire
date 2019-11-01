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

def test_signup_uncharged_user(client):
    # GIVEN a new user (uncharged)
    from shire.models import User
    User.new(username='frodo', email='frodo@marksth.fun', nickname='Frodo', password='P/q2-q4!')

    #   AND he lands on signup page
    r = client.get('/signup/')
    assert r.form.method == 'post'

    # When he submits the form
    r.form.set('username', 'frodo')
    r.form.set('password', 'p/q1-q4?')
    r.form.set('email', 'sam@marksth.fun')
    r = r.form.submit()

    # Then he should be able to refresh all data.
    assert r.status_code == 302
    r = r.follow()
    assert r.request.path == '/signup/confirm/'

def test_signup_fresh_user(client):
    #   AND he lands on signup page
    r = client.get('/signup/')
    assert r.form.method == 'post'

    # When he submits the form
    r.form.set('username', 'frodo')
    r.form.set('password', 'p/q2-q4?')
    r.form.set('email', 'frodo@marksth.fun')
    r = r.form.submit()

    # Then he should be able to refresh all data.
    assert r.status_code == 302
    r = r.follow()
    assert r.request.path == '/signup/confirm/'
