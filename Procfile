web: gunicorn shire.app:app -k gevent -w 8 -b 0.0.0.0:$PORT
worker: celery worker -A shire.worker:celery
