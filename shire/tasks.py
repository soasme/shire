"""
WARNING: The tasks defined in this module is supposed to be idempotent.
It should be safe to re-run these tasks at any time.
"""
import sys

import stripe
from loguru import logger
from flask import current_app, url_for

from shire.core import db, mail, celery

@celery.task
def ping():
    sys.stderr.write("PING SUCCESS")
    sys.stderr.flush()
    return 'PONG'
