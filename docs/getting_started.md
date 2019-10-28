# Getting Started

## Prepare environment

```
$ poetry install
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
$ poetry run python scripts/reset.py
```

## Run

Run the web application at <http://127.0.0.1:5000>.

```bash
$ poetry run flash run
```

## Shell

Open interactive shell.

```bash
$ poetry run flask shell
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
