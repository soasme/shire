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
$ docker-compose build
$ docker-compose up -d
```

## Populate Testing Data

```bash
$ docker-compose exec app python scripts/reset.py
```

## Inspect

Check the website running in local: <http://127.0.0.1:5000>.

## Shell

Open interactive shell.

```bash
$ docker-compose exec app poetry run flask shell
```

## Show Routes

```bash
$ docker-compose exec app poetry run flask routes
```

## Reload

```bash
$ docker-compose exec app poetry run bash
# ps aux|grep gunicorn|head -1|awk '{print $2}'|xargs kill -HUP
# ps aux|grep 'celery worker'|head -1|awk '{print $2}'|xargs kill -HUP
```

## Restart

```bash
$ docker-compose restart app
```

## Add new dependency

```bash
$ docker-compose run --rm app bash
# poetry add blinker
# exit
$ docker-compose build
```

## Ping Worker

```bash
$ docker-compose exec app poetry run flask shell
>>> from shire.tasks import ping
>>> r = ping.delay()
>>> r
<AsyncResult: e62e0305-209c-458f-aa47-cb2fd789f1aa>
>>> r.result
'PONG'
```

You should see logs in `bg` process, something like below.

```
app_1    | 09:27:38 bg.1   | [2019-11-11 09:27:38,683: WARNING/ForkPoolWorker-4] PING SUCCESS
```

You should also see some stats in [flower dashboard](http://127.0.0.1:5555/dashboard) and [flower tasks](http://127.0.0.1:5555/tasks) changed.

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
