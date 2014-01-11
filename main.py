import os
import re
import json
import uuid
import base64
import random
import hashlib
import logging
import urllib2
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
def REDIRECT(uri='/', time=1000):
    return _jinja.get_template('redirect.html').render({
        'uri': uri,
        'time': time,
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
        if not session.user.admin:
            self.error(403)
            self.response.write(JINJA('console-403.html').render())
            return
        values = {
            'session': session,
            'resolve': _APIModelHandler.resolve_properties,
            'encode': APIJSONEncoder().encode,
            'models': models,
        }
        self.response.write(JINJA('console.html').render(values))

def qr_link_callback(uri, rel):
    #if uri.find('google') != -1:
        #url = "%s?%s" % (settings.GOOGLE_CHART_URL, uri)
    return urllib2.urlopen(uri).read()
    #return uri

class QRHandler(webapp2.RequestHandler):
    def get(self):
        makepdf = self.request.get('pdf', '') == 'true'
        markup = JINJA('qr.html').render({
            'amount': int(self.request.get('amount', 0)),
            'uuid': uuid,
            'i': 0,
            'script': ''
        })
        if makepdf:
            self.response.headers['Content-Type'] = 'application/pdf'
            pisa.CreatePDF(markup, self.response, link_callback=qr_link_callback)
        else:
            self.response.write(markup)

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

class CronHandler(webapp2.RequestHandler):
    def get(self, action):
        if action == 'prune':
            for session in models.Session.all():
                if datetime.datetime.utcnow() > session.expiration or session.closed:
                    session.delete()
        else:
            self.error(404)
            return

datetime_format = '%Y-%m-%d %H:%M:%S.%f'
date_format = '%Y-%m-%d'

class APIJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime(datetime_format)
        elif isinstance(obj, datetime.date):
            return obj.strftime(date_format)
        elif isinstance(obj, db.Key):
            return str(obj)
        else:
            return json.JSONEncoder.default(self, obj)

class APIJSONDecoder(json.JSONDecoder):
    def decode(self, obj):
        result = None
        try:
            result = datetime.strptime(obj, date_format).date
            result = datetime.strptime(obj, datetime_format)
        except: pass
        if result: return result
        return json.JSONDecoder.decode(self, obj)

class _APIHandler(webapp2.RequestHandler):
    _secure = True
    _elevated = False
    def route(self, action):
        if self._secure:
            token = self.request.get('token', None)
            session = self.session_from_token(token)
            if not session or (self._elevated and not session.user.admin):
                self.error(403)
                return

        arguments = self.request.arguments()

        self.args = {}
        
        for argument in arguments:
            self.args[argument] = self.argDecode(argument, self.request.get(argument))
        if 'pk' in arguments:
            self.args['value'] = self.argDecode(self.args['name'], self.args['value'])

        logging.info('ARGS ' + repr(self.args))

        function = 'api_' + action
        if hasattr(self, function):
            getattr(self, function)()
        else:
            self.error(404)
    post = route
    get = route

    @staticmethod
    def argDecode(key, value):
        if key == 'password':
            return hashlib.md5(value).hexdigest()
        if value == 'true':
            return True
        if value == 'false':
            return False
        return value

    @staticmethod
    def resolve_properties(instance):
        out = {}
        properties = instance.properties()
        for name in properties:
            if name == 'password': continue
            out[name] = getattr(instance, name)
        out["id"] = instance.key()
        return out

    @staticmethod
    def session_from_token(token):
        if not token: return None

        #session = models.Session.all().filter('token =', token).get()
        try:
            session = models.Session.get(token)
        except db.BadKeyError:
            return None

        if not session: return None

        if session.closed: return None

        if datetime.datetime.utcnow() > session.expiration:
            session.closed = True
            session.put()
            return None

        return session

    def session(self):
        return self.session_from_token(self.request.get('token', ''))

class _APIModelHandler(_APIHandler):
    _model = object
    def api_create(self):
        valid = self._model.properties().keys()
        fields = {}
        args = self.request.arguments()
        for arg in args:
            if arg == 'token': continue
            if not arg in valid:
                logging.info('MISSING ' + arg)
                self.error(401)
                return
            value = self.request.get(arg)
            if arg == 'password':
                value = hashlib.md5(value).hexdigest()
            elif arg == 'admin':
                value = True if value == 'true' else False
            fields[arg] = value
        instance = self._model(**fields)
        instance.put()
        json.dump({
            'id': instance.key()
        }, self.response, cls=APIJSONEncoder)

    def api_get(self):
        args = self.request.arguments()
        data = None
        if 'id' in args:
            instancekey = self.request.get('id')
            try:
                instance = self._model.get(instancekey)
            except db.BadKeyError:
                self.error(404)
                return
            except db.KindError:
                self.error(401)
                return
            data = self.resolve_properties(instance)
        elif 'ids' in args:
            data = []
            try:
                keylist = json.loads(self.request.get('ids'))
            except ValueError:
                self.error(401)
                return
            for key in keylist:
                try:
                    instance = self._model.get(key)
                    data.append(self.resolve_properties(instance))
                except:
                    data.append(None)
        else:
            nolimit = self.request.get('nolimit', '') == 'true'
            runlimit = 100
            if nolimit:
                runlimit = None
            data = [self.resolve_properties(model) for model in self._model.all().run(limit=runlimit)]
            #json.dump(models, self.response, skipkeys=True, cls=APIJSONEncoder)
        json.dump(data, self.response, skipkeys=True, cls=APIJSONEncoder)

    def api_query(self):
        valid = self._model.properties().keys()
        args = self.request.arguments()
        args.remove('token')
        if not args:
            self.error(401)
            return
        query = self._model.all()
        for arg in args:
            if not arg in valid:
                self.error(401)
                return
            query = query.filter(arg + ' =', self.request.get(arg, ''))
        # if not query.get():
        #     self.error(404)
        #     return
        json.dump(
            [self.resolve_properties(instance) for instance in query],
        self.response, skipkeys=True, cls=APIJSONEncoder)

    def api_consoleupdate(self):
        args = self.args
        instancekey = args['pk']

        try:
            instance = self._model.get(instancekey)
        except db.BadKeyError:
            self.error(404)
            return
        except db.KindError:
            self.error(401)
            return

        prop = args['name']
        value = args['value']

        if not prop in self._model.properties().keys():
            self.error(401)
            return

        setattr(instance, prop, value)
        instance.put()

class APISessionHandler(_APIHandler):
    _secure = False
    def api_begin(self):
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
            'token': str(session.key()),
            'provider': {
                'name_prefix': user.name_prefix,
                'name_first': user.name_first,
                'name_middle': user.name_middle,
                'name_last': user.name_last,
                'name_suffix': user.name_suffix,
            }
        }))

    def api_end(self):
        token = self.request.get('token', '')
        if not token:
            self.error(404)
            return

        #session = session_get(token)
        session = _APIHandler.session_from_token(token)
        if not session:
            self.error(403)
            return

        session.closed = True
        session.put()

class APIProviderHandler(_APIModelHandler):
    _elevated = True
    _model = models.Provider

class APIClientHandler(_APIModelHandler):
    _model = models.Client

class APITicketHandler(_APIModelHandler):
    _model = models.Ticket        

#Delegating the various handlers to their respective paths
app = webapp2.WSGIApplication([
    ('/', IndexHandler),
    ('/console', ConsoleHandler),
    ('/console/qr', QRHandler),
    ('/login', ConsoleLoginHandler),
    ('/cron/(\w+)', CronHandler),
    ('/api/session_(\w+)', APISessionHandler),
    ('/api/provider_(\w+)', APIProviderHandler),
    ('/api/client_(\w+)', APIClientHandler),
    ('/api/ticket_(\w+)', APITicketHandler),
], debug=True)