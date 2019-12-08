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

## Export Requirements

```bash
$ docker-compose exec app bash
$ echo "# updated `date`." > requirements.txt && poetry show|awk '{print $1 "==" $2}' >> requirements.txt
```

## Export Supervisor Conf

Export Procfile to supervisor.d conf.

```bash
$ docker-compose exec app poetry run honcho export supervisord data/supervisor.d --app=shire --log=/var/www/shire/shared/logs
```

## Use Stripe CLI

Docs: <https://stripe.com/docs/stripe-cli>.

With the help of stripe CLI, we can let stripe call webhook without using a third-party tunnel.
The stripe listening process is not enabled in procfile by default.
When needed, please do yourself by following below procedure.

```bash
$ docker-compose exec app poetry run bash
[shire@ed3254aa11b6 current]$ stripe login

[shire@ed3254aa11b6 current]$ stripe listen --forward-to http://127.0.0.1:5000/customer/hook/
```

Or, if you have logged in:

```bash
$ docker-compose exec app stripe listen --forward-to http://127.0.0.1:5000/customer/hook/
```

Note that you don't need this in production, instead, you should configure webhook in Stripe dashboard: <https://dashboard.stripe.com/test/webhooks>.

You can also view events at <https://dashboard.stripe.com/test/events>.

## Manually Re-Poll Payments

```bash
$ docker-compose exec app poetry run flask shell
>>> from shire.tasks import *
>>> poll_payments.delay()
<AsyncResult: 7d7ee242-e84a-4e66-abca-97a56de0e47f>
```

Or,

```bash
$ docker-compose exec app poetry run celery -A shire.worker:celery call shire.tasks.poll_payments
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
