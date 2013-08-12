#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import uuid
import hashlib
import logging
import datetime

import webapp2
import jinja2

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import blobstore

from models import Administrator, Provider, Patient

_path = os.path.dirname(__file__) or os.getcwd() #Guaranteed current directory

#Create a jinja environment for loading templates from the /views directory
_jinja = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(_path, 'views')),
    extensions=['jinja2.ext.autoescape']
)


JINJA = _jinja.get_template #To further simplify matters

#Facilitates simpler redirection templating
#   -   I use a redirection template so I can redirect with javascript
#       and avoid form data conflicts that I've had in the past.    
def REDIRECT(uri):
    return _jinja.get_template('redirect.html').render({'location': uri})

#Complicated abstraction to fetch the current admin
def admin_get(instance):
    assert isinstance(instance, webapp2.RequestHandler)
    user = users.get_current_user()
    if user and users.is_current_user_admin():
        user = Administrator.all().filter('master =', True).get()
        if not user:
            #This will only be triggered in the event that; A. The current user
            #   is signed in using a Google account that is granted
            #   administrative priveleges over the GAE app.
            #   B. There is not a master account already in the datastore
            #   for said user to access.
            user = Administrator(
                id=uuid.uuid4().hex,
                username='master',
                password='null',
                firstname='Master',
                lastname='Key',
                master=True
            )
            user.put()
    else:
        #If there is not a Google account logged in or the account does
        #   not have administrative priveleges, it will default to checking
        #   for a session key, and the even one is found, it will try to
        #   match it up to a user in the datastore.
        session = instance.request.cookies.get('clarity-admin', None)
        if session:
            user = Administrator.all().filter('session =', session).get()

    return user

#Handler for the index page *highlights "IndexHandler"*
class IndexHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write(_jinja.get_template('index.html').render())

#Handler for the admin console.
#   -   facilitates the logging in of admins
#   -   passes the user data to the console HTML template
class ConsoleHandler(webapp2.RequestHandler):
    def get(self):
        user = admin_get(self)
        if not user:
            self.redirect('/login')
            return
        values = {
            'user': user,
            'logout_url': '/login?logout=1' if not user.master else users.create_logout_url(dest_url='/'),
            'Administrator': Administrator,
            'Provider': Provider,
            'Patient': Patient
        }
        self.response.write(JINJA('console.html').render(values))

#Handler for logging in admins and providers
#   -   currently only works for admins
#   -   I'll add more comments later because right now I'm too hungry and sleepy
class LoginHandler(webapp2.RequestHandler):
    def get(self):
        if self.request.get('logout', None):
            self.response.delete_cookie('clarity-admin')
            self.response.write(_jinja.get_template('redirect.html').render({
                'location': '/'
            }))
        else:
            values = {
                'adminlogin': users.create_login_url(dest_url='/console')
            }
            self.response.write(_jinja.get_template('login.html').render(values))

    def post(self):
        username = self.request.get('username', None)
        password = self.request.get('password', None)
        if not (username or password): self.error(403)
        digest = hashlib.md5(password).hexdigest()
        user = Administrator.all().filter('username =', username).filter('password =', digest).get()
        if user:
            session = uuid.uuid4().hex
            user.session = session
            user.put()
            self.response.set_cookie(
                'clarity-admin',
                value=session,
                path='/',
                expires=datetime.datetime.now() + datetime.timedelta(days=1)
            )
            #self.response.write(_redirect.format('/console'))
            #self.redirect('/console')
            self.response.write(_jinja.get_template('redirect.html').render({
                'location': '/console'
            }))
        else:
            self.error(403)

#Delegating the various handlers to their respective paths
app = webapp2.WSGIApplication([
    ('/', IndexHandler),
    ('/console', ConsoleHandler),
    ('/login', LoginHandler),
], debug=True)
