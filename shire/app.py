from dotenv import find_dotenv, load_dotenv

from shire.core import create_app

load_dotenv(find_dotenv())
app = create_app()
