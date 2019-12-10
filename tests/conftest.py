import os
import pytest
from webtest import TestApp

@pytest.fixture
def app():
    from shire.core import create_app
    from dotenv import find_dotenv, load_dotenv
    load_dotenv(find_dotenv())
    os.environ['TESTING'] = 'True'
    os.environ['SITE_DOMAIN'] = 'localhost'
    return create_app()

@pytest.fixture
def client(app):
    from shire.core import db

    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
            yield TestApp(app)
            db.session.rollback()
            db.drop_all()
