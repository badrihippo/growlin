from flask import Flask, render_template
from flask.ext.admin import Admin
from flask.ext.security import Security, PeeweeUserDatastore, login_required
from models import *

app = Flask(__name__)
admin = Admin(app)

app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'super-secret'

# Setup Flask-Security
user_datastore = PeeweeUserDatastore(db, User, Role, UserRoles)
security = Security(app, user_datastore)

# Create a user to test with
@app.before_first_request
def create_user():
    for Model in (Group, Role, User, UserRoles):
        Model.drop_table(fail_silently=True)
        Model.create_table(fail_silently=True)
    g = Group.create(name='Test')
    user_datastore.create_user(name='Hippo', password='pass', group=g)

@app.route('/')
def home():
    return render_template('index.htm')
    
@app.route('/user/<username>/')
def user(username):
    return render_template('base.htm', username=username)
if __name__ == '__main__':
    app.run()
