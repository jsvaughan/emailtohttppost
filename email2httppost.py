import logging, email, urllib
from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from google.appengine.ext.webapp.util import run_wsgi_app
import os
from poster.encode import MultipartParam, multipart_encode

class PostToUrl(InboundMailHandler):
    def receive(self, mail_message):
        concatenated_to =  mail_message.to if isinstance(mail_message.to, basestring) else ','.join(mail_message.to)
        body =  ''.join([body.decode() for content_type, body in mail_message.bodies(content_type='text/plain')])

        params = [MultipartParam('sender', value=mail_message.sender),
                  MultipartParam('to', concatenated_to),
                  MultipartParam('body', value=body),
        ]

        if hasattr(mail_message, 'subject'):
            MultipartParam('subject', value=mail_message.subject),

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

app = webapp.WSGIApplication([PostToUrl.mapping()], debug=True)
