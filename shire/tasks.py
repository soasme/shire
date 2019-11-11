from flask import current_app

from shire.core import db, mail, celery
from shire.models import User

@celery.task
def provision_user_account(session=None, email=None, *args, **kwargs):
    user_email = email or session['customer_email']
    assert user_email, 'no email detected.'
    user = User.present(user_email)
    # TODO: generate an url
    mail.send_mail(**{
        'from_': current_app.config('MAIL_FROM'),
        'to': [email],
        'subject': f'Welcome to {current_app.config["SITE_NAME"]}',
        'html': f'''
<p>This is your registration link: <a href="{ url }">{ url }</a></p>.
<p>If you can't click the link, please copy this link to your browser.</p>.
<p>If you encounter a problem, you can ask via {current_app.config['SUPPORT_EMAIL']}.</p>
<p></p>
<p>Best regards,</p>
<p>{current_app.config['SITE_NAME']}</p>
        '''
    })
