from flask.ext.wtf import Form
from wtforms import (TextField, PasswordField, HiddenField, IntegerField, SelectField, validators)
from .models import get_item_types

class UsernamePasswordForm(Form):
    username = TextField('Username')
    password = PasswordField('Password')

class AccessionForm(Form):
    accession = TextField('Accession')

class AccessionTypeForm(Form):
    accession = TextField('Accession',
        validators=[validators.DataRequired()])
    item_type=SelectField('Item type',
        choices=[(i,i) for i in get_item_types()])
class AccessionItemForm(Form):
    accession = HiddenField('Accession',
        validators=[validators.DataRequired()])
    item = HiddenField('Item ID',
        validators=[validators.DataRequired()])
