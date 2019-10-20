# Getting Started

## Prepare environment

```
$ python3 -mvenv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ vi .env # update env vars
```

An example of minimal `.env`:

```
FLASK_DEBUG=True
FLASK_APP=shire/app.py
SECRET_KEY=42
DATABASE_URL=sqlite:////tmp/shire.db
```

## Populate Testing Data

```bash
$ PYTHONPATH=. python scripts/reset.py
```

## Run

Run the web application at <http://127.0.0.1:5000>.

```bash
$ flash run
```

## Shell

Open interactive shell.

```bash
$ flask shell
```

## Update HeyFrodo

For site admins, add `heroku` remote.

```bash
$ git remote add heroku https://git.heroku.com/heyfrodo.git
```

Deploy (require `heroku` cli installed):

```bash
$ heroku login
$ git push heroku master
```
