# Getting Started

## Prepare environment

```
$ cp sample.env .env
$ vi .env # update env vars
```

An example of minimal `.env`:

```
SECRET_KEY=42
DATABASE_URL=sqlite:////tmp/shire.db
FLASK_DEBUG=True
FLASK_APP=shire/app.py
```

## Start

Run the marksthfun stack:

```bash
$ docker-compose up -d
```

## Populate Testing Data

```bash
$ docker-compose exec web poetry run python scripts/reset.py
```

## Inspect

Check the website running in local: <http://127.0.0.1:5000>.

## Shell

Open interactive shell.

```bash
$ docker-compose exec web poetry run flask shell
```

## Show Routes

```bash
$ docker-compose exec web poetry run flask routes
```

## Update Frodo

(For admin only)

For site admins, add `heroku` remote.

```bash
$ git remote add heroku https://git.heroku.com/heyfrodo.git
```

Deploy (require `heroku` cli installed):

```bash
$ heroku login
$ git push heroku master
```
