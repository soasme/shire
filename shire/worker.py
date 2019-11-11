from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())

from shire.core import create_celery
create_celery()

from shire.core import celery
