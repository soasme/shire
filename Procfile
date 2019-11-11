web: gunicorn shire.app:app -k gevent -w 8 -b 0.0.0.0:$PORT
bg: celery worker -A shire.worker:celery -n bg@%h
cron: celery beat  -A shire.worker:celery -s=cron.db --pidfile=''
bgm: celery flower -A shire.worker:celery --address=0.0.0.0 --port=$FLOWER_PORT
