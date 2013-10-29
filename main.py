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
import json
import uuid
import base64
import random
import hashlib
import logging
import datetime
import mimetypes

import webapp2
import jinja2

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import blobstore

import models

import ppk

_path = os.path.dirname(__file__) or os.getcwd() #Guaranteed current directory
_pool = ppk.Pool()
_pool.include(os.path.join(_path, 'ppk'))

#Create a jinja environment for loading templates from the /views directory
_jinja = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(_path, 'views')),
    extensions=['jinja2.ext.autoescape']
)


JINJA = _jinja.get_template #To further simplify matters

#Facilitates simpler redirection templating
#   -   I use a redirection template so I can redirect with javascript
#       and avoid form data conflicts that I've had in the past.    
def REDIRECT(uri='/', time=2000, body='<h1 class="fg-color-red">Redirecting...</h1>'):
    return _jinja.get_template('redirect.html').render({
        'uri': uri,
        'time': time,
        'body': body
    })

#Complicated abstraction to fetch the current admin
def admin_get(instance):
    assert isinstance(instance, webapp2.RequestHandler)
    user = users.get_current_user()
    logging.info('CURRENTUSER ' + str(user))
    if user and users.is_current_user_admin():
        user = Administrator.all().filter('master =', True).get()
        logging.info('CURRENTADMIN ' + str(user))
        if not user:
            #This will only be triggered in the event that; A. The current user
            #   is signed in using a Google account that is granted
            #   administrative priveleges over the GAE app.
            #   B. There is not a master account already in the datastore
            #   for said user to access.
            user = Administrator(
                #id=uuid.uuid4().hex,
                username='master',
                password='null',
                name='Master Key',
                master=True
            )
            user.put()
            logging.info('ADJUSTED ' + str(user))
        return user
    else:
        #If there is not a Google account logged in or the account does
        #   not have administrative priveleges, it will default to checking
        #   for a session key, and the even one is found, it will try to
        #   match it up to a user in the datastore.
        session = instance.request.cookies.get('clarity-admin', None)
        logging.info('SESSION ' + str(session))
        if session:
            user = Administrator.all().filter('session =', session).get()
            logging.info('SESSIONUSER ' + str(user))
            return user
    return None

def user_get(instance):
    assert isinstance(instance, webapp2.RequestHandler)
    user = users.get_current_user()

#Handler for the index page *highlights "IndexHandler"*
class IndexHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write(JINJA('index.html').render())

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

class DummyHandler(webapp2.RequestHandler):
    def post(self):
        #self.redirect(blobstore.create_upload_url())
        blob = models.Blobby()
        blob.data = db.Blob(self.request.get('msg'))
        blob.put()

    '''def post(self):
        prov = models.Provider(
            name_first = self.request.get('name_first'),
            name_last = self.request.get('name_last'),
            username = 'null',
            password = 'null',
            admin = True
        )
        prov.put()'''

class PPKHandler(webapp2.RequestHandler):
    def get(self, path):
        self.response.headers['Content-Type'] = mimetypes.guess_type(path)[0]
        self.response.write(_pool.read(path))

#Handler for logging in admins and providers
#   -   currently only works for admins
#   -   I'll add more comments later because right now I'm too hungry and sleepy
'''
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
            logging.info('SESSIONADJUSTED ' + session)
            user.put()
            self.response.set_cookie(
                'clarity-admin',
                value=session,
                path='/',
                expires=datetime.datetime.now() + datetime.timedelta(days=1)
            )
            #self.response.write(_redirect.format('/console'))
            #self.redirect('/console')
            #self.response.write(_jinja.get_template('redirect.html').render({
            #    'location': '/console'
            #}))
            self.response.write(REDIRECT('/console'))
        else:
            self.error(403)

class DebugHandler(webapp2.RequestHandler):
    def get(self):
        Administrator(
            username='anonymous',
            password='294de3557d9d00b3d2d8a1e6aab028cf', #anonymous
            name='Foo Bar',
            master=False
        ).put()

        Provider(
            username='jkevork',
            password='f9f16d97c90d8c6f2cab37bb6d1f1992', #doctor
            name='Jack Kevorkian',
            location='Roanoke, VA', #This should be lat/long coordinates but I'm lazy so...
            active=True
        ).put()

        Patient(
            name='Samuel Gillispie',
            date_birth=datetime.date(1994, 6, 3),
            location='Roanoke, VA', #Same as before, but I'm still lazy
            sex='male'
        ).put()

        logging.info('DUMMIES CREATED')

class DBHandler(webapp2.RequestHandler):
    fields = {
        Administrator: Administrator.properties(),
        Provider: Provider.properties(),
        Patient: Patient:properties(),
    }
    def get(self):
        data = json.loads(self.request.get('data', default_value='{}'))
        keys = data.get('keys', [])
        fields = data.get('fields', [])
        assert isinstance(keys, list) and isinstance(fields, list) #you niggas better not screw up
        output = []
        for key in keys:
            model = db.get(key)
            model_out = {}
            for k in model.properties():
                model_out[k] = str(getattr(model, k))
            model_out['key'] = key
            output.append(model_out)
        self.response.write(json.dumps(output, indent=4, sort_keys=True).replace('\n', '<br>'))

    def post(self):
        model = self.model_lookup[model.lower()]
'''
#Delegating the various handlers to their respective paths
app = webapp2.WSGIApplication([
    ('/', IndexHandler),
    ('/ppk/(.*)', PPKHandler),
    ('/console', ConsoleHandler),
    ('/howmany', DummyHandler),
    #('/api/', APIHandler)
    #('/login', LoginHandler),
    #('/debug', DebugHandler),
    #(r'/db', DBHandler),
], debug=True)