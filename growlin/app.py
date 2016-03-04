import os 
from flask import Flask
from flask.ext.admin import Admin
from flask.ext.principal import Principal

app = Flask(__name__)
try:
    app.config.from_pyfile('../instance/config.py')
except:
    print 'Unable to load ../instance/config.py'
    print 'Searching for OpenShift environment variables...'
    if os.environ.has_key('OPENSHIFT_APP_NAME'):
        print 'Detected app: %s. Loading configuration variables...'
        app.config['SECRET_KEY'] = 'abcdef'
    
        app.config['MONGODB_DB'] = os.environ.get('OPENSHIFT_APP_NAME')
        app.config['MONGODB_HOST'] = os.environ.get('OPENSHIFT_MONGODB_DB_HOST')
        app.config['MONGODB_PORT'] = os.environ.get('OPENSHIFT_MONGODB_DB_PORT')
        app.config['MONGODB_USERNAME'] = os.environ.get('OPENSHIFT_MONGODB_DB_USERNAME')
        app.config['MONGODB_PASSWORD'] = os.environ.get('OPENSHIFT_MONGODB_DB_PASSWORD')
        
        app.config['GROWLIN_USE_PEEWEE'] = False
        app.config['DEBUG'] = False
    else:
        print 'No OpenShift app detected. Attempt to run with default config.'

# Flag to use peewee driver instead of MongoEngine
if not app.config.has_key('GROWLIN_USE_PEEWEE'):
    app.config['GROWLIN_USE_PEEWEE'] = False

if app.config['GROWLIN_USE_PEEWEE']:
    from flask.ext.peewee.db import Database
    from peewee import DoesNotExist
    db = Database(app)
    db.DoesNotExist = DoesNotExist
else:
    from flask.ext.mongoengine import MongoEngine
    db = MongoEngine()
    db.init_app(app)
