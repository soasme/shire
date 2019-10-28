from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())

from celery.signals import worker_process_init
from shire.core import create_celery
worker_process_init.connect(create_celery)

from shire.core import celery
