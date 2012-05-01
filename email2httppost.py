import logging, email, urllib
from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from google.appengine.ext.webapp.util import run_wsgi_app

class LogSenderHandler(InboundMailHandler):
    def receive(self, mail_message):
        logging.info("Received a message from: " + mail_message.sender)
        body = mail_message.bodies('text/plain').next()[1].decode()
        form_fields = {
            "title": mail_message.subject,
            "body": body,
            "email": mail_message.sender
        }
        form_data = urllib.urlencode(form_fields)
        url = 'http://where.to.send.it'
        result = urlfetch.fetch(url=url,
            payload=form_data,
            method=urlfetch.POST,
            headers={'Content-Type': 'application/x-www-form-urlencoded'})


app = webapp.WSGIApplication([LogSenderHandler.mapping()], debug=True)
