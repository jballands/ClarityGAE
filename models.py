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
    session = db.StringProperty()

class Client(db.Model):
    name_prefix = db.StringProperty(required=False)
    name_first = db.StringProperty(required=True)
    name_middle = db.StringProperty(required=False)
    name_last = db.StringProperty(required=True)
    name_suffix = db.StringProperty(required=False)

    dateofbirth = db.DateProperty(required=True)

    sex = db.StringProperty(required=True)
    location = db.StringProperty(required=True)

    headshot = blobstore.BlobReferenceProperty()

class Ticket(db.Model):
    isopen = db.BooleanProperty(required=False, default=True)
    opened = db.DateTimeProperty(auto_now_add=True)
    closed = db.DateTimeProperty(required=False)

    qrid = db.StringProperty(required=False)

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