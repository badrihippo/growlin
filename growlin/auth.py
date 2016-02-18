from flask import render_template, redirect, url_for, request, flash, current_app, session
from flask.ext.login import LoginManager, login_required, current_user, login_user, logout_user
from flask.ext.principal import Principal, Permission, RoleNeed, UserNeed, Identity, AnonymousIdentity, identity_changed, identity_loaded
from .app import app
from .forms import UsernamePasswordForm
from .models import *

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

principals = Principal(app)

@login_manager.user_loader
def load_user(userid=None, username=None):
    try:
        if userid is not None:
	    if app.config['GROWLIN_USE_PEEWEE']:
                user = User.objects.get(User.id == userid)
	    else:
		user = User.objects.get(id=userid)
        elif username is not None:
	    if app.config['GROWLIN_USE_PEEWEE']:
	        user = User.objects.get(User.username == username)
	    else:
		user = User.objects.get(username=username)
    except db.DoesNotExist:
	return None
    return user

# Setup principals

@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity
    if hasattr(current_user, 'id'):
	identity.provides.add(UserNeed(current_user.id))

    # Add roles
    if hasattr(current_user, 'roles'):
	for role in current_user.roles:
	    identity.provides.add(RoleNeed(role.name))

def next_is_valid(next):
	'''Takes in a URL and ensures that it is a valid redirect'''
	return True #TODO: Perform acutal validation!

@app.route('/login/', methods=['GET', 'POST'])
def login():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us.
    form = UsernamePasswordForm()
    group_dict = {}
    # Map users to groups
    for user in User.objects:
	if group_dict.has_key(user.group.name):
	    group_dict[user.group.name].append(user)
	else:
	    group_dict[user.group.name] = [user]
    # Serialize to list
    group_list = [{'name': k, 'users': v} for k,v in group_dict.items()]
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

		# Inform Principal of changed identity
		identity_changed.send(
		    current_app._get_current_object(),
		    identity=Identity(str(user.id)))

	        flash('Logged in successfully.')

	        next = request.args.get('next')
	        if not next_is_valid(next):
	            return abort(400)

	        return redirect(next or url_for('home'))
	# Default to returning login page
    return render_template('login.htm', form=form, group_list=group_list)

@app.route('/logout/')
@login_required
def logout():
    logout_user()
    flash('You are now logged out.')

    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type'):
	session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(
        current_app._get_current_object(),
	identity=AnonymousIdentity())

    return redirect(request.args.get('next') or url_for('login'))
