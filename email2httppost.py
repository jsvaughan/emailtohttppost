import logging, email, urllib
from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from google.appengine.ext.webapp.util import run_wsgi_app
import os

class PostToUrl(InboundMailHandler):
    def receive(self, mail_message):
        body =  ''.join([body.decode() for content_type, body in mail_message.bodies(content_type='text/plain')])
        form_fields = {
            "title": mail_message.subject,
            "body": body,
            "email": mail_message.sender
        }
        form_data = urllib.urlencode(form_fields)

        urlfetch.fetch(url=os.environ.get('DESTINATION_URL'),
            payload=form_data,
            method=urlfetch.POST,
            headers={'Content-Type': 'application/x-www-form-urlencoded'})


app = webapp.WSGIApplication([PostToUrl.mapping()], debug=True)
