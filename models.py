from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import blobstore

class Administrator(db.Model):
    id = db.StringProperty(required=True)
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True) #This will only be a password digest. Storing passwords in plaintext is just bad practice.
    firstname = db.StringProperty(required=True)
    lastname = db.StringProperty(required=True)
    master = db.BooleanProperty(required=True)

    session = db.StringProperty()

class Provider(db.Model):
    id = db.StringProperty(required=True)
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True) #This will only be a password digest. Storing passwords in plaintext is just bad practice.
    firstname = db.StringProperty(required=True)
    lastname = db.StringProperty(required=True)

    location = db.StringProperty(required=False)
    active = db.BooleanProperty(required=True)
    datetime_started = db.DateTimeProperty(auto_now_add=True)
    datetime_terminated = db.DateTimeProperty(required=False)

    signature = blobstore.BlobReferenceProperty()
    #This will be one tricky bitch to program

    session = db.StringProperty()

class Patient(db.Model):
    id = db.StringProperty(required=True)
    firstname = db.StringProperty(required=True)
    lastname = db.StringProperty(required=True)

    date_birth = db.DateProperty()
    location = db.StringProperty()
    sex = db.StringProperty()
    picture = blobstore.BlobReferenceProperty() #This one too

    datetime_first = db.DateTimeProperty(auto_now_add=True)

    providers = db.StringListProperty(db.Key)
    services = db.StringListProperty(str)