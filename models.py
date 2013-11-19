import uuid
import datetime

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import blobstore

class Blobby(db.Model):
    data = db.BlobProperty(required=False)

class Provider(db.Model):
    #General properties:
    name_prefix = db.StringProperty(required=False)
    name_first = db.StringProperty(required=True)
    name_middle = db.StringProperty(required=False)
    name_last = db.StringProperty(required=True)
    name_suffix = db.StringProperty(required=False)

    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True)

    admin = db.BooleanProperty(required=True)

    headshot = blobstore.BlobReferenceProperty()
    #This will be one tricky bitch to program

    #Housekeeping:
    datetime_created = db.DateTimeProperty(auto_now_add=True)
    datetime_terminated = db.DateTimeProperty(required=False)

class Session(db.Model):
    token = db.StringProperty(required=False)
    creation = db.DateTimeProperty(auto_now_add=True)
    expiration = db.DateTimeProperty(required=False)
    user = db.ReferenceProperty(Provider, required=True)
    api = db.BooleanProperty(required=True)

    closed = db.BooleanProperty(required=False)

    def __init__(self, *args, **kwargs):
        #kwargs['token'] = uuid.uuid4().hex
        #kwargs['closed'] = False
        db.Model.__init__(self, *args, **kwargs)
        if not self.token:
            self.token = uuid.uuid4().hex
            self.closed = False

    def close(self):
        self.closed = True
        self.put()

class Client(db.Model):
    name_prefix = db.StringProperty(required=False)
    name_first = db.StringProperty(required=True)
    name_middle = db.StringProperty(required=False)
    name_last = db.StringProperty(required=True)
    name_suffix = db.StringProperty(required=False)
    #dateofbirth = db.DateProperty(required=True)
    dateofbirth = db.StringProperty(required=True)
    sex = db.StringProperty(required=True)
    location = db.StringProperty(required=False)

    headshot = blobstore.BlobReferenceProperty(required=False)

class Ticket(db.Model):
    isopen = db.BooleanProperty(required=False, default=True)
    opened = db.DateTimeProperty(auto_now_add=True)
    closed = db.DateTimeProperty(required=False)

    qrcode = db.StringProperty(required=False)

    client = db.ReferenceProperty(Client, required=True, collection_name='tickets')

class Service(db.Model):
    name = db.StringProperty(required=True)
    quantity = db.IntegerProperty(required=True)
    provider = db.ReferenceProperty(Provider, required=True, collection_name='services')

class Loan(db.Model):
    disbursed = db.FloatProperty(required=True)
    owed = db.FloatProperty(required=False)
    date_due = db.FloatProperty(required=False)
    opened = db.DateTimeProperty(auto_now_add=True)
    closed = db.DateTimeProperty(required=False)

    client = db.ReferenceProperty(Client, required=True, collection_name='loans')

#Relationship Models:
'''
class TicketProvider(db.Model):
    ticket = db.ReferenceProperty(Ticket, required=True, collection_name='tickets')
    provider = db.ReferenceProperty(Provider, required=True, collection_name='providers')
'''

class TicketService(db.Model):
    ticket = db.ReferenceProperty(Ticket, required=True, collection_name='tickets')
    service = db.ReferenceProperty(Service, required=True, collection_name='services'),

class ClientProvider(db.Model):
    client = db.ReferenceProperty(Client, required=True, collection_name='clients')
    provider = db.ReferenceProperty(Provider, required=True, collection_name='providers')