from flask.ext.admin import Admin, BaseView, expose
from .app import app
from .auth import Permission, RoleNeed
from .models import *

if app.config['GROWLIN_USE_PEEWEE']:
    from flask.ext.admin.contrib.peewee import ModelView
else:
    from flask.ext.admin.contrib.mongoengine import ModelView

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
    form_create_rules = ('accession', 'title', 'subtitle', 'keywords', 'comments', 'campus_location', 'price', 'price_currency', 'receipt_date', 'source')
    edit_modal = True

class AdminModelBorrowing(BaseModelView):
    form_excluded_columns = ['copydata_type', 'copydata_id']
    form_ajax_refs = {
    'user': {
        'fields': ['username', 'name', 'email'],
        'page_size': 10
    },
    }

admin.add_view(AdminModelPublication(Item, name='All Items', category='Registry'))

if app.config['GROWLIN_USE_PEEWEE']:
    class AdminModelTypeItem(BaseModelView):
        item_type = 'item'
        def get_query(self):
            try:
                my_type = ItemType.get(item_type=self.item_type)
                return self.model.select().where(self.model.item_type == my_type)
            except ItemType.DoesNotExist:
                print 'Warning: Returning all items'
                return self.model.select()
    class AdminModelBookItem(AdminModelTypeItem):
        item_type = 'book'
    class AdminModelPeriodicalItem(AdminModelTypeItem):
        item_type = 'periodical'

    admin.add_view(AdminModelBookItem(model=BookItem, name='Books', category='Registry'))
    admin.add_view(AdminModelPeriodicalItem(model=PeriodicalItem, name='Periodicals', category='Registry'))

else:
    admin.add_view(AdminModelPublication(BookItem, name='Books', category='Registry'))
    admin.add_view(AdminModelPublication(PeriodicalItem, name='Periodicals', category='Registry'))

admin.add_view(AdminModelUser(User, name='Users', category='Accounts'))
admin.add_view(BaseModelView(UserGroup, name='Groups', category='Accounts'))
admin.add_view(BaseModelView(UserRole, name='Roles', category='Accounts'))
admin.add_view(AdminModelBorrowing(BorrowPast, name='Past borrowings', category='Accounts'))

if app.config['GROWLIN_USE_PEEWEE']:
    admin.add_view(BaseModelView(ItemType, name='Item types', category='Metadata'))

admin.add_view(BaseModelView(Publisher, name='Publishers', category='Metadata'))
admin.add_view(BaseModelView(PublishPlace, name='Publish locations', category='Metadata'))
admin.add_view(BaseModelView(CampusLocation, name='Campus locations', category='Metadata'))
admin.add_view(BaseModelView(Genre, name='Genres', category='Metadata'))
admin.add_view(BaseModelView(Currency, name='Currencies', category='Metadata'))
