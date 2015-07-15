from flask import Flask, render_template, redirect, abort, flash, request, url_for
from flask_wtf import Form
import wtforms as wtf
from flask.ext.login import LoginManager, login_required, login_user, logout_user
from flask.ext.principal import Principal, Permission, RoleNeed
from flask.ext.admin import Admin
#from flask.ext.security import Security, PeeweeUserDatastore, login_required
from models import *

app = Flask(__name__)
admin = Admin(app)

app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'super-secret'

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(userid=None, username=None):
    try:
        if userid is not None:
            user = User.get(User.id == userid)
        elif username is not None:
	    user = User.get(User.username == username)
    except pw.DoesNotExist:
	return None
    return user
    
# Setup Flask-Principal
principals = Principal(app)

# Load test data from models.py
create_test_data = app.before_first_request(create_test_data)


class LoginForm(Form):
    username = wtf.TextField('Username')
    password = wtf.PasswordField('Password')

def next_is_valid(next):
	'''Takes in a URL and ensures that it is a valid redirect'''
	return True #TODO: Perform acutal validation!

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us.
    form = LoginForm()
    group_list = Group.select()
    if form.validate_on_submit():
        # Login and validate the user.
        user = load_user(username=form.username.data)
        if (not user) or (user.password and user.password != form.password.data):
            msg = 'Invalid username or password'
            if form.errors.has_key('password'):
                form.errors['password'].append(msg)
            else:
                form.errors['password'] = [msg]
        else:
		# All OK. Log in the user.
	        login_user(user)
	
	        flash('Logged in successfully.')
	
	        next = request.args.get('next')
	        if not next_is_valid(next):
	            return abort(400)
	
	        return redirect(next or url_for('home'))
	# Default to returning login page        
    return render_template('login.htm', form=form, group_list=group_list)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You are now logged out.')
    return redirect(url_for('home'))
    

@app.route('/')
def home():
    return render_template('index.htm')
    
@app.route('/user/<username>/')
def user(username):
    return render_template('base.htm', username=username)
if __name__ == '__main__':
    app.run()
