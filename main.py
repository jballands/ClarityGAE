import os
import re
import json
import math
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
import yaml

from google.appengine.ext import db
from google.appengine.api import users
#from google.appengine.ext import blobstore

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
            self.redirect('/')
            return
        if not session.user.admin:
            self.error(403)
            self.response.write(JINJA('console-403.html').render())
            return

        sampledata = {}

        #Generate some generic statistics for demonstration of the home screen
        totalcount = float(models.Client.all().count())

        malecount = float(models.Client.all().filter('sex =', 'male').count())
        femalecount = float(models.Client.all().filter('sex =', 'female').count())

        sampledata['male'] = math.floor(malecount / totalcount * 100.0)
        sampledata['female'] = math.floor(femalecount / totalcount * 100.0)

        values = {
            'session': session,
            'resolve': _APIModelHandler.resolve_properties,
            'encode': APIJSONEncoder().encode,
            'models': models,
            'sampledata': sampledata,
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

'''class ConsoleLoginHandler(webapp2.RequestHandler):
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
                self.response.write(JINJA('login.html').render(values))'''

class CronHandler(webapp2.RequestHandler):
    def get(self, action):
        if action == 'prune':
            for session in models.Session.all():
                if datetime.datetime.utcnow() > session.expiration or session.closed:
                    session.delete()
        else:
            self.error(404)
            return

datetime_format = '%Y-%m-%d %H:%M:%S'
date_format = '%Y-%m-%d'

class APIJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime(datetime_format)
        elif isinstance(obj, datetime.date):
            return obj.strftime(date_format)
        elif isinstance(obj, db.Key):
            return str(obj)
        elif isinstance(obj, db.Model):
            properties = obj.properties()

            #Resolve the object to a dictionary
            #(only works for explicitly defined properties)
            kvs = db.to_dict(obj)

            #Get implicitly defined references (this is such a bitch)
            for attr in dir(obj):
                try:
                    if isinstance(getattr(obj, attr), db.Query):
                        kvs[attr] = list(getattr(obj, attr).run(keys_only=True))
                except db.ReferencePropertyResolveError:
                    continue
            
            kvs.pop('password', None)
            kvs.pop('binary', None)

            for key in kvs:
                if key == 'dateofbirth':
                    kvs[key] = kvs[key].date()

            kvs['id'] = obj.key()
            return kvs
        else:
            try:
                return json.JSONEncoder.default(self, obj)
            except TypeError:
                return 'CANNOT_SERIALIZE'

#class APIJSONDecoder(json.JSONDecoder):
#    def decode(self, obj):
#        logging.info('DECODING ' + repr(obj))
#        result = None
#        try:
#            result = datetime.datetime.strptime(obj, date_format).date()
#            result = datetime.datetime.strptime(obj, datetime_format)
#        except ValueError: pass
#        if result: return result
#        return super(APIJSONDecoder, self).decode(obj)

class _APIHandler(webapp2.RequestHandler):
    _errors = {}
    with open('errors.yaml', 'r') as errorfile:
        _errors = yaml.load(errorfile.read())

    _secure = True
    
    _restricted = ['remove',]

    def route(self, action, method='post'):
        raw_arguments = self.request.arguments()
        self.args = {}
        self.is_json = True
        
        if method == 'post':
            logging.info('REQUEST_IS_JSON')
            logging.info('REQUEST_JSON_BODY ' + repr(self.request.body))
            try:
                self.args = json.load(self.request.body_file)
                #for key in self.args:
                #    if key in models.date_properties:
                #        self.args[key] = datetime.datetime.strptime(self.args[key], date_format).date()
                #    elif key in models.datetime_properties:
                #        self.args[key] = datetime.datetime.strptime(self.args[key], datetime_format)
            except ValueError:
                if self.request.body:
                    logging.info('REQUEST_JSON_INVALID')
                    return self.error(400.104)
        elif method == 'get':
            self.args = {key: self.request.get(key) for key in self.request.arguments()}

        #if 'qrcode' in self.args:
        #    if not re.match(r'clarity[a-f0-9]{32}$', self.args['qrcode']):
        #        return self.error(400.105)

        #Remove the token argument and log it to the console
        self.token = self.args.pop('token', None)
        logging.info('REQUEST_TOKEN ' + repr(self.token))
        
        #Verify the arguments
        self.args_verify()
        
        #Post processing option because x-editable never makes it easy
        #if self.args.get('postprocess', False):
        #    self.args_postprocess()

        #Log the arguments to assist with error debugging
        logging.info('REQUEST_ARGS ' + repr(self.args))

        if self._secure:
            self.session = self.session_from_token(self.token)

            if not self.session:
                return self.error(403.201)

            if action in self._restricted and not self.session.user.admin:
                return self.error(403.202)

        function = 'api_' + action
        if hasattr(self, function):
            result = getattr(self, function)()
            if result: self.respond_json(result)
        else:
            self.error(404)
    post = route
    
    def get(self, *args, **kwargs):
        kwargs['method'] = 'get'
        self.route(*args, **kwargs)

    def error(self, floatcode):
        intcode = int(math.floor(floatcode))
        webapp2.RequestHandler.error(self, intcode)

        logging.warning('ERROR_CODE ' + repr(floatcode))

        if floatcode in self._errors:
            #json.dump(self._errors[floatcode], self.response, cls=APIJSONEncoder)
            self.response.write(self._errors[floatcode])
            logging.warning('ERROR_MESSAGE ' + repr(self._errors[floatcode]))

    def respond_json(self, data):
        json.dump(data, self.response, cls=APIJSONEncoder, skipkeys=True)
    
    def args_verify(self):
        for key in self.args:
            value = self.args[key]
            
            if key == 'qrcode':
                if not re.match(r'clarity[a-f0-9]{32}$', value): return self.error(400.105)

    @staticmethod
    def argDecode(key, value):
        #if key == 'password':
        #    return hashlib.md5(value).hexdigest()
        if key == 'qrcode':
            return value if re.match(r'clarity[a-f0-9]{32}$', value) is not None else None
        if key == 'binary':
            return base64.b64decode(value)
        if key == 'dateofbirth':
            return datetime.datetime.strptime(value, date_format).date()

        try:
            result = datetime.datetime.strptime(value, datetime_format)
            return result
        except: pass

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
            try:
                out[name] = getattr(instance, name)
            except db.ReferencePropertyResolveError:
                return []
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
        return self.session_from_token(self.args.get('token', ''))

class _APIModelHandler(_APIHandler):
    _model = object
    
    format_datetime = '%Y-%m-%d %H:%M:%S'
    format_date = '%Y-%m-%d'
    
    def args_verify(self):
        _APIHandler.args_verify(self)
        self.args_postprocess()
    
    def args_postprocess(self):
        #X-Editable doesn't have types, only strings, so this intelligently casts them
        for key in self.args:
            try:
                prop = self._model.properties()[key]
                value = self.args[key]
                logging.info('BEFORE ' + key + ' ' + repr(value))
                
                if isinstance(prop, db.IntegerProperty):
                    value = int(value)
                elif isinstance(prop, db.BooleanProperty):
                    if not isinstance(value, bool):
                        value = True if value == 'true' else False
                elif isinstance(prop, db.DateProperty):
                    value = datetime.datetime.strptime(value, self.format_date).date()
                elif isinstance(prop, db.DateTimeProperty):
                    value = datetime.datetime.strptime(value, self.format_datetime)
                
                logging.info('AFTER ' + repr(value))
                self.args[key] = value
            except KeyError: pass

    def _get_instances(self, throw_errors=True):
        #If the singular ID argument is specified, return dat
        if 'id' in self.args:
            instance_key =  self.args.get('id')

            #Do a cheap instance get. If there are errors, instance will stay none.
            instance = None
            try:
                instance = self._model.get(instance_key)
            except: pass

            #If the instance actually doesn't exist, erorrrrrrrrrr
            if not instance: return self.error(404.100) if throw_errors else None

            #If you've made it this far, return the fruits of your labor
            return instance

        #If a list of IDs is give, do dat
        if 'ids' in self.args:
            keylist = self.args.get('ids')

            #Return those results. THANK YOU GOOGLE FOR MAKING THIS EASY!
            return db.get(keylist)

        #Wow you really fucked up if it got this far
        return None
    
    def get_instances(self, throw_errors=True):
        #If the singular ID argument is specified, return dat
        instances = []
        if 'id' in self.args:
            instance_key =  self.args.pop('id')

            #Do a cheap instance get. If there are errors, instance will stay none.
            instance = None
            try:
                instance = self._model.get(instance_key)
            except: pass

            #If the instance actually doesn't exist, erorrrrrrrrrr
            if not instance: return self.error(404.100) if throw_errors else None

            #If you've made it this far, return the fruits of your labor
            instances.append(instance)

        #If a list of IDs is give, do dat
        if 'ids' in self.args:
            keylist = self.args.pop('ids')

            #Return those results. THANK YOU GOOGLE FOR MAKING THIS EASY!
            instances = db.get(keylist)

        #Return dat shit (or None)
        self.instances = instances
        return instances

    def api_create(self):
        properties = self._model.properties()
        valid = properties.keys()
        fields = {}
        #self.args_postprocess()
        #args = self.request.arguments()
        args = self.args.keys()
        for arg in args:
            if arg == 'token': continue
            if not arg in valid:
                logging.info('INVALID ' + arg + ' ' + repr(self._model))
                self.error(401)
                return
            value = self.args[arg]
            if isinstance(properties[arg], db.ReferenceProperty):
                if not isinstance(value, db.Model):
                    foreignModel = properties[arg].reference_class
                    foreignKey = value
                    try:
                        foreignInstance = foreignModel.get(foreignKey)
                    except:
                        self.error(401)
                        return
                    value = foreignInstance
            elif arg == 'password':
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
        #Use that shiny new builtin method and the shiny new return system
        #instances = self.get_instances()
        return self._get_instances()

    def api_query(self):
        valid = self._model.properties().keys()
        args = self.args
        #args.pop('token')

        runlimit = int(args.pop('limit', 100))
        runoffset = int(args.pop('offset', 0))

        query = self._model.all()
        for arg in args:
            if not arg in valid:
                self.error(401)
                return
            query = query.filter(arg + ' =', args[arg])
            logging.info('QUERY_BY {0}={1}'.format(arg, args[arg]))
        
        if hasattr(self._model, '_order'):
            query = query.order(self._model._order)

        try:
            data = {
                'count': query.count(),
                'results': query.fetch(
                    limit = runlimit,
                    offset = runoffset
                )
            }
        except db.NeedIndexError:
            return self.error(500.201)

        json.dump(data, self.response, skipkeys=True, cls=APIJSONEncoder)

    def api_remove(self):
        #Use that shiny new method I made
        given = self._get_instances()
        
        if isinstance(given, (db.Model, list)):
            db.delete(given)

    def api_update(self):
        #Get the ID, turn it into an instance, and deal with any errors
        instances = self.get_instances()
        
        #Retrieve request arguments
        arguments = self.args
        
        #Retrieve valid model properties
        valid_properties = self._model.properties().keys()

        #Iterate through given arguments and update the instance
        for instance in instances:
            for key in arguments:
                if not key in valid_properties: return self.error(401.2)
                setattr(instance, key, arguments[key])
            
            #Save the updates
            instance.put()

    def api_consoleupdate(self):
        oldargs = self.args
        
        name = oldargs['name']
        value = oldargs['value']
        
        #if isinstance(self._model.properties()[name], db.IntegerProperty):
        #    value = int(value)
        
        self.args = {
            'id': oldargs['pk'],
            name: value
        }
        
        #self.args_postprocess()
        self.args_verify()
        return self.api_update()

class APISessionHandler(_APIModelHandler):
    _model = models.Session
    _secure = False

    def api_begin(self):
        username = self.args.get('username', '')
        password = self.args.get('password', '')
        api_session = not self.args.get('console', '')

        user = models.Provider.all().filter('username =', username).get()
        if not user:
            self.error(403.101)
            return

        password_hash = hashlib.md5(password).hexdigest()
        if not password_hash == user.password:
            self.error(403.102)
            return

        session = models.Session(
            user = user,
            api = api_session
        )
        session.expiration = session.creation + datetime.timedelta(days=1)
        session.put()

        #self.response.write(json.dumps({
        #    'token': str(session.key()),
        #    'provider': session.user
        #}))
        json.dump({
            'token': session.key(),
            'provider': session.user
        }, self.response, skipkeys=True, cls=APIJSONEncoder)

    def api_end(self):
        token = self.token
        if not token:
            return
        session = _APIHandler.session_from_token(token)
        if not session:
            return

        session.closed = True
        session.put()

class APIProviderHandler(_APIModelHandler):
    _model = models.Provider
    _restricted = [
        'create',
        'remove',
        'console_update'
    ]

class APIHeadshotHandler(_APIModelHandler):
    _model = models.Headshot
    def api_download(self):
        instancekey = self.args.get('id', '')
        try:
            instance = self._model.get(instancekey)
        except db.BadKeyError:
            self.error(404)
            return
        except db.KindError:
            self.error(401)
            return

        self.response.headers['Content-Type'] = str(instance.mimetype)
        self.response.write(instance.binary)

class APIClientHandler(_APIModelHandler):
    _model = models.Client
    def api_create(self):
        image = self.args.pop('binary', None)
        if image:
            if self.is_json:
                image = base64.b64decode(image)
            #headshot = models.Headshot(binary=db.Blob(image))
            headshot = models.Headshot()
            #headshot.binary = db.Blob(image)
            headshot.binary = image
            headshot.put()
            self.args['headshot'] = headshot
        _APIModelHandler.api_create(self)

class APITicketHandler(_APIModelHandler):
    _model = models.Ticket
    def api_create(self):
        if models.Ticket.all().filter('qrcode =', self.args['qrcode']).get(): return self.error(400.106)
        _APIModelHandler.api_create(self)
    
    def api_close(self):
        instances = self._get_instances()
        if not isinstance(instances, (list, tuple)):
            instances = [instances, ]
        
        for ticket in instances:
            if not ticket.closed:
                ticket.closed = datetime.datetime.utcnow()
                ticket.put()
    
    def api_update(self):
        _APIModelHandler.api_update(self)
        for instance in self.instances:
            if not instance.closed:
                closing = True
                for service in instance.services:
                    value = getattr(instance, service)
                    if value == 1:
                        closing = False
                        break
                if closing:
                    instance.closed = datetime.datetime.utcnow()
                    instance.put()

class APIAPPHandler(_APIHandler):
    def api_tickets_by_ticket(self):
        try:
            source_ticket = models.Ticket.all().filter('qrcode =', self.args['qrcode']).get()
        except: return self.error(400.201)
        
        if not source_ticket: return self.error(404.201)

        output = {}
        output['patient'] = source_ticket.client
        output['tickets'] = []

        for ticket in source_ticket.client.tickets:
            output['tickets'].append({
                'id': ticket.key(),
                'opened': ticket.opened,
                'closed': ticket.closed
            })

        self.respond_json(output)

#class APIServiceHandler(_APIModelHandler):
#    _model = models.Service

class DummyHandler(_APIHandler):
    _secure = False
    def api_echo(self):
        return self.args

    def api_dummies(self):
        client = models.Client(
            name_first = 'testman',
            name_last = 'doop doop',
            dateofbirth = datetime.date(day=2, month=2, year=1990),
            sex = "male"
        )
        client.put()
        for i in range(6):
            models.Ticket(
                client = client,
                qrcode = str(i * 10)
            ).put()

class UserDummyHandler(_APIHandler): pass

#Delegating the various handlers to their respective paths
app = webapp2.WSGIApplication([
    ('/', IndexHandler),
    ('/console', ConsoleHandler),
    ('/console/qr', QRHandler),
    #('/login', ConsoleLoginHandler),
    ('/cron/(\w+)', CronHandler),
    ('/api/session_(\w+)', APISessionHandler),
    ('/api/provider_(\w+)', APIProviderHandler),
    ('/api/headshot_(\w+)', APIHeadshotHandler),
    ('/api/client_(\w+)', APIClientHandler),
    ('/api/ticket_(\w+)', APITicketHandler),
    #('/api/service_(\w+)', APIServiceHandler),
    ('/test_(\w+)', DummyHandler),
    ('/usertest_(\w+)', UserDummyHandler),

    #A few app-only handlers
    ('/api/app/(\w+)', APIAPPHandler)
], debug=True)