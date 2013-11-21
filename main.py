import os
import re
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
def REDIRECT(uri='/', time=2000, body=None):
    return _jinja.get_template('redirect.html').render({
        'uri': uri,
        'time': time,
        'body': body
    })

def user_get(instance):
    sessionkey = instance.request.cookies.get('clarity-console-session', None)
    if sessionkey:
        logging.info(sessionkey)
        session = models.Session.get(sessionkey)
        if session:
            return session.user
    return None

def session_get(token):
    if not token: return None

    session = models.Session.all().filter('token =', token).get()
    if not session: return None

    if session.closed: return None

    if datetime.datetime.utcnow() > session.expiration:
        session.closed = True
        session.put()
        return None

    return session

#Handler for the index page *highlights "IndexHandler"*
class IndexHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write(JINJA('index.html').render())

#Handler for the admin console.
#   -   facilitates the logging in of admins
#   -   passes the user data to the console HTML template
class ConsoleHandler(webapp2.RequestHandler):
    def get(self):
        session = _APIHandler.session_from_token(self.request.cookies.get('clarity-console-session', ''))
        if not session:
            self.redirect('/login')
            return
        values = {
            'session': session
        }
        self.response.write(JINJA('console.html').render(values))

class QRHandler(webapp2.RequestHandler):
    def get(self): pass

class DummyHandler(webapp2.RequestHandler):
    def post(self):
        #self.redirect(blobstore.create_upload_url())
        blob = models.Blobby()
        blob.data = db.Blob(self.request.get('msg'))
        blob.put()

    def get(self):
        models.Provider(
            name_first='Samuel',
            name_middle='Paige',
            name_last='Gillispie',
            name_suffix='II',

            username='spgill',
            password='5f4dcc3b5aa765d61d8327deb882cf99',

            admin=True,
        ).put()

        models.Provider(
            name_first='Jonathan',
            name_last='Ballands',

            username='jonathan',
            password='5f4dcc3b5aa765d61d8327deb882cf99',

            admin=True,
        ).put()

        self.response.write('New users inserted!')

# class PPKHandler(webapp2.RequestHandler):
#     def get(self, path):
#         self.response.headers['Content-Type'] = mimetypes.guess_type(path)[0]
#         self.response.write(_pool.read(path))

#Handler for logging in admins and providers
#   -   I'll add more comments later because right now I'm too hungry and sleepy
class ConsoleLoginHandler(webapp2.RequestHandler):
    def get(self):
        session = _APIHandler.session_from_token(self.request.cookies.get('clarity-console-session', ''))
        if self.request.get('close', '') == 'true':
            if session:
                session.close()
            self.response.delete_cookie('clarity-console-session')
            self.response.write(REDIRECT('/'))
        else:
            if session:
                self.response.write(REDIRECT('/console'))
            else:
                values = {
                    'request': self.request
                }
                #self.response.write(_jinja.get_template('login.html').render(values))
                self.response.write(JINJA('login.html').render(values))

    def post(self):
        username = self.request.get('username', None)
        password = self.request.get('password', None)

        if not (username or password):
            self.error(403)
            self.redirect('/login?error=403')
            return

        user = models.Provider.all().filter('username =', username).get()
        if user:
            digest = hashlib.md5(password).hexdigest()
            if digest != user.password:
                self.error(403)
                self.redirect('/login?error=403')
                return
            timeout = datetime.timedelta(minutes=60)
            session = models.Session(
                user = user,
                api = False
            )
            session.expiration = session.creation + timeout
            session.put()
            self.response.set_cookie(
                'clarity-console-session',
                value=session.token,
                path='/',
                #expires=datetime.datetime.now() + timeout
            )
            logging.info('SUCCESS')
            self.response.write(REDIRECT('/console'))
        else:
            self.error(403)
            self.redirect('/login?error=403')
            return

class CronHandler(webapp2.RequestHandler):
    def get(self, action):
        if action == 'prune':
            for session in models.Session.all():
                if datetime.datetime.utcnow() > session.expiration or session.closed:
                    session.delete()
        else:
            self.error(404)
            return

class _APIEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return str(obj)
        else:
            return json.JSONEncoder.default(self, obj)

datetime_format = '%Y-%m-%d %H:%M:%S.%f'
date_format = '%Y-%m-%d'
class _APIDecoder(json.JSONDecoder):
    def decode(self, obj):
        result = None
        try:
            result = datetime.strptime(obj, date_format).date
            result = datetime.strptime(obj, datetime_format)
        except: pass
        if result: return result
        return json.JSONDecoder.decode(self, obj)

class _APIHandler(webapp2.RequestHandler):
    _model = object

    def route(self, action):
        token = self.request.get('token', None)
        if not self.session_from_token(token):
            self.error(403)
            return

        function = 'api_' + action
        if hasattr(self, function):
            getattr(self, function)()
        else:
            self.error(404)
    post = route
    get = route

    def api_create(self):
        valid = self._model.properties().keys()
        fields = {}
        args = self.request.arguments()
        for arg in args:
            if arg == 'token': continue
            if not arg in valid:
                self.error(401)
                return
            fields[arg] = self.request.get(arg)
        instance = self._model(**fields)
        instance.put()
        json.dump({
            'id': str(instance.key())
        }, self.response)

    def api_get(self):
        args = self.request.arguments()
        if not 'id' in args:
            models = [self.resolve_properties(model) for model in self._model.all()]
            json.dump(models, self.response, skipkeys=True, cls=_APIEncoder)
        else:
            instancekey = self.request.get('id')
            try:
                instance = self._model.get(instancekey)
            except db.BadKeyError, db.KindError:
                self.error(404)
                return
            if not instance:
                self.error(404)
                return
            json.dump(self.resolve_properties(instance), self.response, skipkeys=True, cls=_APIEncoder)

    @staticmethod
    def resolve_properties(instance):
        out = {}
        properties = instance.properties()
        for name in properties:
            out[name] = getattr(instance, name)
        out["id"] = str(instance.key())
        return out

    @staticmethod
    def session_from_token(token):
        if not token: return None

        session = models.Session.all().filter('token =', token).get()
        if not session: return None

        if session.closed: return None

        if datetime.datetime.utcnow() > session.expiration:
            session.closed = True
            session.put()
            return None

        return session

class SessionHandler(webapp2.RequestHandler):
    def get(self, action):
        function = 'session_' + action
        if hasattr(self, function):
            getattr(self, function)()
        else:
            self.error(404)

    def session_begin(self):
        username = self.request.get('username', '')
        password = self.request.get('password', '')
        api_session = not self.request.get('console', '')

        user = models.Provider.all().filter('username =', username).get()
        if not user:
            self.error(403)
            return

        password_hash = hashlib.md5(password).hexdigest()
        if not password_hash == user.password:
            self.error(403)
            return

        session = models.Session(
            user = user,
            api = api_session
        )
        session.expiration = session.creation + datetime.timedelta(days=1)
        session.put()

        self.response.write(json.dumps({
            'token': session.token,
            'provider': {
                'name_prefix': user.name_prefix,
                'name_first': user.name_first,
                'name_middle': user.name_middle,
                'name_last': user.name_last,
                'name_suffix': user.name_suffix,
            }
        }))

    def session_end(self):
        token = self.request.get('token', '')
        if not token:
            self.error(404)
            return

        session = session_get(token)
        if not session:
            self.error(403)
            return

        session.closed = True
        session.put()

class APIProviderHandler(_APIHandler):
    _model = models.Provider

class APIClientHandler(_APIHandler):
    _model = models.Client

class APITicketHandler(_APIHandler):
    _model = models.Ticket

#Delegating the various handlers to their respective paths
app = webapp2.WSGIApplication([
    ('/', IndexHandler),
    ('/console', ConsoleHandler),
    ('/console/qr', QRHandler),
    ('/howmany', DummyHandler),
    ('/login', ConsoleLoginHandler),
    ('/cron/(\w+)', CronHandler),
    ('/api/session_(\w+)', SessionHandler),
    ('/api/provider_(\w+)', APIProviderHandler),
    ('/api/client_(\w+)', APIClientHandler),
    ('/api/ticket_(\w+)', APITicketHandler)
    #('/api/', APIHandler)
    #('/login', LoginHandler),
    #('/debug', DebugHandler),
    #(r'/db', DBHandler),
], debug=True)