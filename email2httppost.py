import logging, email, urllib
from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from google.appengine.ext.webapp.util import run_wsgi_app
import os
from poster.encode import MultipartParam, multipart_encode

class PostToUrl(InboundMailHandler):
    def receive(self, mail_message):
        params = [MultipartParam('email', value=mail_message.sender), MultipartParam('title', value=mail_message.subject)]

        body =  ''.join([body.decode() for content_type, body in mail_message.bodies(content_type='text/plain')])
        params.append(MultipartParam('body', value=body))

        if hasattr(mail_message, 'attachments') and mail_message.attachments:
            attachments = mail_message.attachments
            # Only process the first
            name, content = attachments[0]
            params.append(MultipartParam(
                "image",
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
