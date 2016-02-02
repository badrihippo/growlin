from flask import Flask
from flask.ext.admin import Admin
from flask.ext.principal import Principal

app = Flask(__name__)
app.config.from_pyfile('../instance/config.py')

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
