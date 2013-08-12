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

_path = os.path.dirname(__file__) or os.getcwd()
_jinja = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(_path, 'views')),
    extensions=['jinja2.ext.autoescape']
)

def admin_get(instance):
    assert isinstance(instance, webapp2.RequestHandler)
    user = users.get_current_user()
    if user and users.is_current_user_admin():
        user = Administrator.all().filter('master =', True).get()
        if not user:
            user = Administrator(
                id=uuid.uuid4().hex,
                username='master',
                password='null',
                firstname='Master',
                lastname='Key',
                master=True
            )
            user.put()
            user2 = Administrator(
                id=uuid.uuid4().hex,
                username='testing',
                password='81dc9bdb52d04dc20036dbd8313ed055',
                firstname='John',
                lastname='Doe',
                master=False
            )
            user2.put()
    else:
        session = instance.request.cookies.get('clarity-admin', None)
        if session:
            user = Administrator.all().filter('session =', session).get()

    return user

class IndexHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write(_jinja.get_template('index.html').render())

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
        self.response.write(_jinja.get_template('console.html').render(values))

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

app = webapp2.WSGIApplication([
    ('/', IndexHandler),
    ('/console', ConsoleHandler),
    ('/login', LoginHandler),
], debug=True)
