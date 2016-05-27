import os 
from flask import Flask
from flask.ext.admin import Admin
from flask.ext.principal import Principal
from flask_admin_material import setup_templates
from flask.ext.mongoengine import MongoEngine

app = Flask(__name__)
try:
    app.config.from_pyfile('../instance/config.py')
except:
    print 'Unable to load ../instance/config.py'
    print 'Searching for OpenShift environment variables...'
    if os.environ.has_key('OPENSHIFT_APP_NAME'):
        print 'Detected app: %s. Loading configuration variables...' % os.environ.get('OPENSHIFT_APP_NAME')
        app.config['SECRET_KEY'] = 'abcdef'
    
        app.config['MONGODB_DB'] = os.environ.get('OPENSHIFT_APP_NAME')
        app.config['MONGODB_HOST'] = os.environ.get('OPENSHIFT_MONGODB_DB_HOST')
        app.config['MONGODB_PORT'] = os.environ.get('OPENSHIFT_MONGODB_DB_PORT', 0)
        app.config['MONGODB_USERNAME'] = os.environ.get('OPENSHIFT_MONGODB_DB_USERNAME')
        app.config['MONGODB_PASSWORD'] = os.environ.get('OPENSHIFT_MONGODB_DB_PASSWORD')
        
        app.config['DEBUG'] = False
    else:
        print 'No OpenShift app detected. Attempt to run with default config.'

db = MongoEngine()
db.init_app(app)

app = setup_templates(app)
