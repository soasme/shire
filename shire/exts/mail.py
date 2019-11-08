import requests

class Mailgun:

    def __init__(self, key, base_url, timeout=10):
        self.key = key
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()

    def send_mail(self, from_, to, subject, text):
        return self.session.post(f'{self.base_url}/messages', data={
            'from': from_,
            'to': to,
            'subject': subject,
            'text': text
        }, auth=('api', self.key), timeout=self.timeout)


class Mail:

    def __init__(self, app=None):
        if not app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.app.extensions['mail'] = self

        if app.config.get('MAILGUN_API_KEY'):
            self.mailer = Mailgun(
                key=app.config['MAILGUN_API_KEY'],
                base_url=app.config.get('MAILGUN_BASE_URL', 'https://api.mailgun.net/v3'),
            )
        else:
            raise ValueError('Missing mailer configurations.')

    def send_mail(self, from_, to, subject, text):
        if not hasattr(self, 'mailer'): raise AttributeError('mailer not initialized.')
        return self.mailer.send_mail(from_, to, subject, text)
