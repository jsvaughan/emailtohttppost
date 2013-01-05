from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from google.appengine.api import mail
import os
from poster.encode import MultipartParam, multipart_encode
from google.appengine.ext import db
import logging
from google.appengine.ext import ereporter

ereporter.register_logger()

class Email(db.Model):
    created = db.DateTimeProperty(auto_now_add=True)
    sender = db.StringProperty(multiline=True)
    to = db.StringProperty(multiline=True)
    cc = db.StringProperty(multiline=True)
    bcc = db.StringProperty(multiline=True)
    subject = db.TextProperty()
    body = db.TextProperty()


class PostToUrl(InboundMailHandler):
    def join_recipients_if_required(self, mail_message_field):
        return mail_message_field if isinstance(mail_message_field, basestring) else ','.join(mail_message_field)

    def receive(self, mail_message):
        sender = mail_message.sender
        to = self.join_recipients_if_required(mail_message.to)
        cc = self.join_recipients_if_required(mail_message.cc) if hasattr(mail_message, 'cc') else None
        bcc = self.join_recipients_if_required(mail_message.bcc) if hasattr(mail_message, 'bcc') else None
        subject = mail_message.subject if hasattr(mail_message, 'subject') else ''
        body = ''.join([body.decode() for content_type, body in mail_message.bodies(content_type='text/plain')])

        try:
            if os.environ.get('COPY_DB'):
                self.persist(sender, to, cc, bcc, subject, body)
        except:
            logging.exception('Error saving email.')

        try:
            if os.environ.get('COPY_EMAIL'):
                self.send_copy(sender, to, cc, bcc, subject, body)
        except:
            logging.exception('Error sending email copy.')

        params = [MultipartParam('sender', value=sender),
                  MultipartParam('to', to),
                  MultipartParam('subject', value=subject),
                  MultipartParam('body', value=body),
        ]

        if hasattr(mail_message, 'attachments') and mail_message.attachments:
            # Only process the first
            name, content = mail_message.attachments[0]
            params.append(MultipartParam(
                'picture',
                filename=name,
                value=content.decode()))

        payloadgen, headers = multipart_encode(params)
        payload = str().join(payloadgen)

        result = urlfetch.fetch(
            url=os.environ.get('DESTINATION_URL'),
            payload=payload,
            method=urlfetch.POST,
            headers=headers,
            deadline=60)

        self.response.out.write('HTTP RESPONSE STATUS: %s<br />' % result.status_code)
        self.response.out.write(result.content)

    def send_copy(self, original_sender, original_to, original_cc, original_bcc, original_subject, original_body):
        to = os.environ.get('COPY_EMAIL_TO')
        sender = os.environ.get('COPY_EMAIL_FROM')
        subject = os.environ.get('COPY_EMAIL_SUBJECT')
        body = 'Sender=%s\nTo=%s\nCc=%s\nBcc=%s\nSubject=%s\n\n%s' % (original_sender, original_to, original_cc, original_bcc, original_subject, original_body)
        mail.send_mail(sender=sender,
            to=to,
            subject=subject,
            body=body)

    def persist(self, sender, to, cc, bcc, subject, body):
        email = Email(sender=sender, to=to, cc=cc, bcc=bcc, subject=subject, body=body)
        email.put()


app = webapp.WSGIApplication([PostToUrl.mapping()], debug=True)
