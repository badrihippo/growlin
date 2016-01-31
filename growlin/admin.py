from flask.ext.admin import Admin, BaseView, expose
from flask_admin.contrib.mongoengine import ModelView
from .app import app
from .auth import Permission, RoleNeed
from .models import *

admin = Admin(app)

admin_permission = Permission(RoleNeed('admin'))

class AdminRegistry(BaseView):
    @expose('/')
    def index(self):
	return self.render('admin/registry_index.htm')
    def is_accessible(self):
	return admin_permission.can()

class BaseModelView(ModelView):
    def is_accessible(self):
	return admin_permission.can()

class AdminModelUser(BaseModelView):
    can_create = True
    column_list = ('username', 'name', 'group', 'active')

class AdminModelPublication(BaseModelView):
    form_create_rules = ('title', 'display_title', 'call_no', 'keywords', 'comments', 'identifier', 'copies')
    form_excluded_columns = ['pubtype', 'pubdata_id']
    edit_modal = True
    #inline_models = (Copy,)

class AdminModelCopy(BaseModelView):
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
class AdminModelBorrowing(BaseModelView):
    form_excluded_columns = ['copydata_type', 'copydata_id']
    form_ajax_refs = {
	'user': {
	    'fields': ['username', 'name', 'email'],
	    'page_size': 10
	},
    }

admin.add_view(AdminModelPublication(Item, name='Publications', category='Registry'))

admin.add_view(BaseModelView(Publisher, name='Publishers', category='Metadata'))
admin.add_view(BaseModelView(PublishPlace, name='Publish locations', category='Metadata'))

admin.add_view(BaseModelView(CampusLocation, name='Places'))

admin.add_view(AdminModelUser(User, name='Users', category='Accounts'))
admin.add_view(BaseModelView(UserGroup, name='Groups', category='Accounts'))
admin.add_view(AdminModelBorrowing(BorrowPast, name='Past borrowings', category='Accounts'))

admin.add_view(BaseModelView(UserRole, name='Roles', category='Admin'))
