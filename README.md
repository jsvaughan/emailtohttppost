emailtohttppost
===============

An appengine app that receives email and sends the email content via http post

e.g. a free alternative to http://mailnuggets.com, http://cloudmailin.com etc

What it does
-------------------------
Any email sent to {string}@{appid}.appspotmail.com becomes a multipart post to a url you specify, with the fields:

email = the sender's email address
title = the email subject lne
body = the email body
image = the first attachment, if present

How to use it
-------------------------

 * Check out
 * Create a google appengine project for it
 * Edit the application name in app.yaml to match your appengine project name
 * Edit app.yaml to set the DESTINATION_URL
 * You can test locally using the GAE development server and the admin console, using the Inbound Mail function (although doesn't allow attachments)
 * Publish to GAE
