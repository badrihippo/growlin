from .app import app
if app.config['GROWLIN_USE_PEEWEE']:
    from modelproxy.peewee_models import *
else:
    from modelproxy.mongoengine import *
