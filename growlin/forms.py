from flask.ext.wtf import Form
from wtforms import (TextField, PasswordField, HiddenField, IntegerField, validators)

class UsernamePasswordForm(Form):
    username = TextField('Username')
    password = PasswordField('Password')

class AccessionForm(Form):
    accession = TextField('Accession')

class AccessionItemForm(Form):
    accession = HiddenField('Accession',
        validators=[validators.DataRequired()])
    item = HiddenField('Item ID',
        validators=[validators.DataRequired()])
