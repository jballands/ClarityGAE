import uuid
import datetime

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import search 
from google.appengine.ext import blobstore

date_properties = [
    'dateofbirth'
]

datetime_properties = [
    'datetime_created',
    'datetime_terminated',
    'creation',
    'expiration',
    'opened',
    'closed'
]

class Headshot(db.Model):
    binary = db.BlobProperty(required=False)
    mimetype = db.StringProperty(required=False, default='image/jpeg')

class _ClarityModel(db.Model):
    _order = None
    _index = None
    _fields = {}
    _document = db.StringProperty(required=False)

class Provider(_ClarityModel):
    _order_search = search.SortExpression(expression="name_last", direction=search.SortExpression.DESCENDING)
    _order_query = "name_last"
    _index = 'provider'
    _fields = {
        'name_prefix': search.TextField,
        'name_first': search.TextField,
        'name_middle': search.TextField,
        'name_last': search.TextField,
        'name_suffix': search.TextField,
    }
    
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

class Session(_ClarityModel):
    #token = db.StringProperty(required=False)
    creation = db.DateTimeProperty(auto_now_add=True)
    expiration = db.DateTimeProperty(required=False)
    user = db.ReferenceProperty(Provider, required=True)
    api = db.BooleanProperty(required=True)
    closed = db.BooleanProperty(required=False, default=False)

    def close(self):
        self.closed = True
        self.put()

class Client(_ClarityModel):
    _order_search = search.SortExpression(expression="name_last", direction=search.SortExpression.DESCENDING)
    _order_query = "name_last"
    _index = 'client'
    _fields = {
        'name_prefix': search.TextField,
        'name_first': search.TextField,
        'name_middle': search.TextField,
        'name_last': search.TextField,
        'name_suffix': search.TextField,
        'dateofbirth': search.DateField,
        'sex': search.AtomField,
        'location': search.TextField,
    }
    
    name_prefix = db.StringProperty(required=False)
    name_first = db.StringProperty(required=True)
    name_middle = db.StringProperty(required=False)
    name_last = db.StringProperty(required=True)
    name_suffix = db.StringProperty(required=False)
    dateofbirth = db.DateProperty(required=True)
    sex = db.StringProperty(required=True)
    location = db.StringProperty(required=False)

    headshot = db.ReferenceProperty(Headshot, required=False)

class Ticket(_ClarityModel):
    _order_search = search.SortExpression(expression="opened", direction=search.SortExpression.ASCENDING)
    _order_query = "-opened"
    _index = 'ticket'
    _fields = {
        "left_leg": search.NumberField,
	    "right_leg": search.NumberField,
	    "left_shin": search.NumberField,
	    "right_shin": search.NumberField,
	    "left_arm": search.NumberField,
	    "right_arm": search.NumberField,

	    "sewing_machine": search.NumberField,
	    "crutches": search.NumberField,
	    "tricycle": search.NumberField,
	    "tea_stand": search.NumberField,
	    "wheelchair": search.NumberField,
	    
	    "loan_status": search.NumberField,
    }
    
    #Basic ticket information and reference properties
    qrcode = db.StringProperty(required=False)
    client = db.ReferenceProperty(Client, required=True, collection_name='tickets')

    #Timestamp properties
    opened = db.DateTimeProperty(auto_now_add=True)
    closed = db.DateTimeProperty(required=False)

    #Service properties
    left_leg = db.IntegerProperty(required=False, default=0)
    right_leg = db.IntegerProperty(required=False, default=0)
    left_shin = db.IntegerProperty(required=False, default=0)
    right_shin = db.IntegerProperty(required=False, default=0)
    left_arm = db.IntegerProperty(required=False, default=0)
    right_arm = db.IntegerProperty(required=False, default=0)

    sewing_machine = db.IntegerProperty(required=False, default=0)
    crutches = db.IntegerProperty(required=False, default=0)
    tricycle = db.IntegerProperty(required=False, default=0)
    tea_stand = db.IntegerProperty(required=False, default=0)
    wheelchair = db.IntegerProperty(required=False, default=0)
    
    loan_status = db.IntegerProperty(required=False, default=0)
    loan_amount = db.IntegerProperty(required=False, default=0)
    
    services = [
        'left_leg',
        'right_leg',
        'left_shin',
        'right_shin',
        'left_arm',
        'right_arm',
        'sewing_machine',
        'crutches',
        'tricycle',
        'tea_stand',
        'wheelchair',
        'loan_status'
    ]

    #Activity log (wip)
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