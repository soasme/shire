import requests

class Shell:

    def send_mail(self, from_, to, subject, html):
        print(f"""Send mail (mailer: shell)
From: {from_}
To: {to}
Subject: {subject}
Html: {html}""")

class Mailgun:

    def __init__(self, key, base_url, domain, timeout=10):
        self.key = key
        self.base_url = base_url
        self.domain = domain
        self.timeout = timeout
        self.session = requests.Session()

    def send_mail(self, from_, to, subject, html):
        return self.session.post(f'{self.base_url}/{self.domain}/messages', data={
            'from': from_,
            'to': to,
            'subject': subject,
            'html': html,
        }, auth=('api', self.key), timeout=self.timeout)


class Mail:

    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        app.extensions['mail'] = self
        self.default_mailer = self.default_sender = Shell()

        if app.config.get('MAILGUN_API_KEY'):
            self.mailer = Mailgun(
                key=app.config['MAILGUN_API_KEY'],
                base_url=app.config.get('MAILGUN_BASE_URL') or 'https://api.mailgun.net/v3',
                domain=app.config['MAILGUN_DOMAIN']
            )
        else:
            self.mailer = self.default_mailer

    def send_mail(self, from_, to, subject, html):
        if not hasattr(self, 'mailer'): raise AttributeError('mailer not initialized.')
        return self.mailer.send_mail(from_, to, subject, html)
