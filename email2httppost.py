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
    message_id = db.StringProperty(multiline=True)
    subject = db.TextProperty()
    body = db.TextProperty()
    html_body = db.TextProperty()

class PostToUrl(InboundMailHandler):
    def recipients_as_string(self, mail_message_field):
        if not mail_message_field:
            return None
        return mail_message_field if isinstance(mail_message_field, basestring) else ','.join(mail_message_field)

    def receive(self, mail_message):
        complete_message = mail_message.original

        sender = mail_message.sender
        to = self.recipients_as_string(mail_message.to) if hasattr(mail_message, 'to') else None
        cc = self.recipients_as_string(mail_message.cc) if hasattr(mail_message, 'cc') else None
        bcc = self.recipients_as_string(complete_message.bcc) if hasattr(complete_message, 'bcc') else None
        message_id = complete_message.get('message-id', None)

        subject = mail_message.subject if hasattr(mail_message, 'subject') else ''
        body = ''.join([body_part.decode() for content_type, body_part in mail_message.bodies(content_type='text/plain')])
        html_body = ''.join([body_part.decode() for content_type, body_part in mail_message.bodies(content_type='text/html')])

        for item in complete_message.items():
            logging.error("%s=%s" % (item[0], item[1]))
        try:
            if os.environ.get('COPY_DB'):
                self.persist(message_id, sender, to, cc, bcc, subject, body, html_body)
        except:
            logging.exception('Error saving email.')

        try:
            if os.environ.get('COPY_EMAIL'):
                self.send_copy(message_id, sender, to, cc, bcc, subject, body, html_body)
        except:
            logging.exception('Error sending email copy.')

        params = [MultipartParam('sender', value=sender),
                  MultipartParam('to', to),
                  MultipartParam('subject', value=subject),
                  MultipartParam('body', value=body),
                  MultipartParam('htmlbody', value=html_body),
        ]

        if cc:
            params.append(MultipartParam('cc', cc))
        if bcc:
            params.append(MultipartParam('bcc', bcc))
        if message_id:
            params.append(MultipartParam('message-id', message_id))

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

    def send_copy(self, message_id, original_sender, original_to, original_cc, original_bcc, original_subject, original_body, html_body):
        to = os.environ.get('COPY_EMAIL_TO')
        sender = os.environ.get('COPY_EMAIL_FROM')
        subject = os.environ.get('COPY_EMAIL_SUBJECT')
        body = 'Message Id=%s\nSender=%s\nTo=%s\nCc=%s\nBcc=%s\nSubject=%s\n\n%s\n\n%s' % (
        message_id, original_sender, original_to, original_cc, original_bcc, original_subject, original_body, html_body)
        mail.send_mail(sender=sender,
            to=to,
            subject=subject,
            body=body)

    def persist(self, message_id, sender, to, cc, bcc, subject, body, html_body):
        email = Email(message_id=message_id, sender=sender, to=to, cc=cc, bcc=bcc, subject=subject, body=body, html_body=html_body)
        email.put()


app = webapp.WSGIApplication([PostToUrl.mapping()], debug=True)
