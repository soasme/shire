from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())

from shire.core import create_app
app = create_app()

from shire.core import celery
