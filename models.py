import uuid
import datetime

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import blobstore

class Headshot(db.Model):
    binary = db.BlobProperty(required=False)
    mimetype = db.StringProperty(required=False, default='image/jpeg')

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

    headshot = db.ReferenceProperty(Headshot, required=False)
    #headshot = blobstore.BlobReferenceProperty()

    #Housekeeping:
    datetime_created = db.DateTimeProperty(auto_now_add=True)
    datetime_terminated = db.DateTimeProperty(required=False)

class Session(db.Model):
    #token = db.StringProperty(required=False)
    creation = db.DateTimeProperty(auto_now_add=True)
    expiration = db.DateTimeProperty(required=False)
    user = db.ReferenceProperty(Provider, required=True)
    api = db.BooleanProperty(required=True)
    closed = db.BooleanProperty(required=False, default=False)

    def close(self):
        self.closed = True
        self.put()

class Client(db.Model):
    name_prefix = db.StringProperty(required=False)
    name_first = db.StringProperty(required=True)
    name_middle = db.StringProperty(required=False)
    name_last = db.StringProperty(required=True)
    name_suffix = db.StringProperty(required=False)
    dateofbirth = db.DateProperty(required=True)
    sex = db.StringProperty(required=True)
    location = db.StringProperty(required=False)

    headshot = db.ReferenceProperty(Headshot, required=False)

class Ticket(db.Model):
    #Basic ticket information and reference properties
    qrcode = db.StringProperty(required=False)
    client = db.ReferenceProperty(Client, required=True, collection_name='tickets')

    #Timestamp properties
    opened = db.DateTimeProperty(auto_now_add=True)
    closed = db.DateTimeProperty(required=False)

    #Service properties
    left_leg = db.BooleanProperty(required=False, default=False)
    right_leg = db.BooleanProperty(required=False, default=False)
    left_shin = db.BooleanProperty(required=False, default=False)
    right_shin = db.BooleanProperty(required=False, default=False)
    left_arm = db.BooleanProperty(required=False, default=False)
    right_arm = db.BooleanProperty(required=False, default=False)

    sewing_machine = db.BooleanProperty(required=False, default=False)
    crutches = db.BooleanProperty(required=False, default=False)
    tricycle = db.BooleanProperty(required=False, default=False)
    tea_stand = db.BooleanProperty(required=False, default=False)
    wheelchair = db.BooleanProperty(required=False, default=False)
    
    loan = db.IntegerProperty(required=False, default=0)

'''
class Service(db.Model):
    name = db.StringProperty(required=True)
    description = db.TextProperty(required=False)
    provider = db.ReferenceProperty(Provider, required=True, collection_name='services')
    ticket = db.ReferenceProperty(Ticket, required=True, collection_name='services')

class Loan(db.Model):
    disbursed = db.FloatProperty(required=True)
    owed = db.FloatProperty(required=False)
    date_due = db.FloatProperty(required=False)
    opened = db.DateTimeProperty(auto_now_add=True)
    closed = db.DateTimeProperty(required=False)

    client = db.ReferenceProperty(Client, required=True, collection_name='loans')
'''