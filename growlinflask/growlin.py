from flask import Flask, render_template, redirect, abort, flash, request, url_for
from flask_wtf import Form
import wtforms as wtf
from flask.ext.login import LoginManager, login_required, login_user, logout_user
from flask.ext.principal import Principal, Permission, RoleNeed
from flask_admin import Admin, BaseView, expose
from flask_admin.form import rules
from flask_admin.contrib.peewee.view import ModelView
from wtfpeewee.orm import model_form
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
#create_test_data = app.before_first_request(create_test_data)


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

# Admin interface
class AdminRegistry(BaseView):
    @expose('/')
    def index(self):
	return self.render('admin/registry_index.htm')
    def is_accessible(self):
	#return current_user.is_authenticated() # add permission check
	return True

class AdminModelUser(ModelView):
    can_create = True
    column_list = ('username', 'name', 'group', 'active')


class AdminModelPublication(ModelView):
    form_create_rules = ('title', 'display_title', 'call_no', 'keywords', 'comments', 'identifier', 'copies')
    form_excluded_columns = ['pubtype', 'pubdata_id']
    edit_modal = True
    inline_models = (Copy,)

class AdminModelCopy(ModelView):
    form_excluded_columns = ['copydata_type', 'copydata_id']
    form_ajax_refs = {
	'item': {
	    'fields': ['title', 'call_no'],
	    'page_size': 10
	},
	'location': {
	    'fields': ['name'],
	    'page_size': 5
	},
    }
class AdminModelBorrowing(ModelView):
    form_excluded_columns = ['copydata_type', 'copydata_id']
    form_ajax_refs = {
	'user': {
	    'fields': ['refnum', 'username', 'name', 'email'],
	    'page_size': 10
	},
	'group': {
	    'fields': ['name'],
	    'page_size': 5,
	},
    }


admin.add_view(AdminModelPublication(Publication, name='Publications', category='Registry'))
admin.add_view(AdminModelCopy(Copy, name='Copies', category='Registry'))

admin.add_view(ModelView(Publisher, name='Publishers', category='Metadata'))
admin.add_view(ModelView(PublishPlace, name='Publish locations', category='Metadata'))

admin.add_view(ModelView(Location, name='Places'))

admin.add_view(AdminModelUser(User, name='Users', category='Accounts'))
admin.add_view(ModelView(Group, name='Groups', category='Accounts'))
admin.add_view(AdminModelBorrowing(Borrowing, name='Borrowings', category='Accounts'))
admin.add_view(AdminModelBorrowing(PastBorrowing, name='Past borrowings', category='Accounts'))

# Publication and Copy extra data

for m in all_pubtypes.union(all_pubcopies):
    # TODO: Remove reference to private _meta property!
    admin.add_view(ModelView(m,
        name=m._meta.verbose_name if hasattr(m._meta, 'verbose_name') else m._meta.name,
	category='Extra Publication Data'))
    
if __name__ == '__main__':
    app.run()
