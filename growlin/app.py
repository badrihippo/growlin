from flask import Flask
from flask.ext.admin import Admin
from flask.ext.principal import Principal

app = Flask(__name__)
app.config.from_pyfile('../instance/config.py')
