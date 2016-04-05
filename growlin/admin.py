from flask.ext.admin import Admin, BaseView, expose
from .util.widgets import AddModelSelect2Widget
from .app import app
from .auth import Permission, RoleNeed
from .models import *

if app.config['GROWLIN_USE_PEEWEE']:
    from flask.ext.admin.contrib.peewee import ModelView
else:
    from flask.ext.admin.contrib.mongoengine import ModelView

admin = Admin(app, template_mode='bootstrap3')

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

class AdminMetadataView(BaseModelView):
    create_modal = True

class AdminModelUser(BaseModelView):
    can_create = True
    column_list = ('username', 'name', 'group', 'active')
    column_searchable_list = ['username', 'name']

class AdminModelPublication(BaseModelView):
    form_excluded_columns = ['borrow_current']
    column_searchable_list = ['title']
    form_ajax_refs = {
    'campus_location': {
        'fields': ['name'],
        'page_size': 5
    },
    'promo_location': {
        'fields': ['name'],
        'page_size': 5
    },
    'price_currency': {
        'fields': ['name'],
        'page_size': 5
    },
    }
    column_list = ('accession', 'title', 'campus_location', 'promo_location')
    can_view_details = True
    create_template = 'admin/overrides/item_edit.htm'
    edit_template = 'admin/overrides/item_edit.htm'
class AdminModelBookItem(AdminModelPublication):
    form_ajax_refs = {
    'publication_publisher': {
        'fields': ['name'],
        'page_size': 10
    },
    'publication_place': {
        'fields': ['name'],
        'page_size': 10
    },
    'authors': {
        'fields': ['name'],
        'page_size': 10
    },
    'editors': {
        'fields': ['name'],
        'page_size': 10
    },
    'illustrators': {
        'fields': ['name'],
        'page_size': 10
    },
    'campus_location': {
        'fields': ['name'],
        'page_size': 5
    },
    'promo_location': {
        'fields': ['name'],
        'page_size': 5
    },
    'price_currency': {
        'fields': ['name'],
        'page_size': 5
    },
    }
    column_list = ('accession', 'title', 'authors', 'editors', 'campus_location', 'promo_location')
    form_args = {
        'price_currency': {
            'widget': AddModelSelect2Widget('/admin/currency/new'),
        },
        'campus_location': {
            'widget': AddModelSelect2Widget('/admin/campuslocation/new'),
        },
        'publication_publisher': {
            'widget': AddModelSelect2Widget('/admin/publisher/new'),
        },
        'publication_place': {
            'widget': AddModelSelect2Widget('/admin/publishplace/new'),
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

admin.add_view(AdminModelPublication(Item, name='All Items', category='Registry'))

if app.config['GROWLIN_USE_PEEWEE']:
    class AdminModelTypeItem(BaseModelView):
        item_type = 'item'
        def get_query(self):
            try:
                my_type = ItemType.get(name=self.item_type)
                return self.model.select().where(self.model.item_type == my_type)
            except ItemType.DoesNotExist:
                print 'Warning: Returning all items'
                return self.model.select()
    class AdminModelBookTypeItem(AdminModelTypeItem, AdminModelBookItem):
        item_type = 'book'
        form_ajax_refs = {
        'publication_publisher': {
            'fields': ['name'],
            'page_size': 10
        },
        'publication_place': {
            'fields': ['name'],
            'page_size': 10
        },
        'author': {
            'fields': ['name'],
            'page_size': 10
            },
        'editor': {
            'fields': ['name'],
            'page_size': 10
        },
        'illustrator': {
            'fields': ['name'],
            'page_size': 10
        },
        'campus_location': {
            'fields': ['name'],
            'page_size': 5
        },
        'promo_location': {
            'fields': ['name'],
            'page_size': 5
        },
        'price_currency': {
            'fields': ['name'],
            'page_size': 5
        },
        }
    class AdminModelPeriodicalTypeItem(AdminModelTypeItem):
        item_type = 'periodical'

    admin.add_view(AdminModelBookTypeItem(model=BookItem, name='Books', category='Registry'))
    admin.add_view(AdminModelPeriodicalTypeItem(model=PeriodicalItem, name='Periodicals', category='Registry'))

else:
    admin.add_view(AdminModelBookItem(BookItem, name='Books', category='Registry'))
    admin.add_view(AdminModelPublication(PeriodicalItem, name='Periodicals', category='Registry'))

admin.add_view(AdminModelUser(User, name='Users', category='Accounts'))
admin.add_view(BaseModelView(UserGroup, name='Groups', category='Accounts'))
admin.add_view(BaseModelView(UserRole, name='Roles', category='Accounts'))
admin.add_view(AdminModelBorrowing(BorrowPast, name='Past borrowings', category='Accounts'))

admin.add_view(BaseModelView(ItemType, name='Item types', category='Metadata'))

admin.add_view(AdminMetadataView(Publisher, name='Publishers', category='Metadata'))
admin.add_view(AdminMetadataView(PublishPlace, name='Publish locations', category='Metadata'))
admin.add_view(AdminMetadataView(CampusLocation, name='Campus locations', category='Metadata'))
admin.add_view(AdminMetadataView(Genre, name='Genres', category='Metadata'))
admin.add_view(AdminMetadataView(Currency, name='Currencies', category='Metadata'))
admin.add_view(AdminMetadataView(Creator, name='Creators', category='Metadata'))

admin.add_view(BaseModelView(PeriodicalSubscription, name='Periodical subscriptions', category='More'))
