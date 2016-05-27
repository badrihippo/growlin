from flask.ext.admin import Admin, BaseView, expose
from .util.widgets import AddModelSelect2Widget
from .app import app
from .auth import Permission, RoleNeed
from .models import *
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

def _check_unique_accession(accession):
    return Item.objects.filter(accession=accession).count() == 0

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
    form_args = {
        'accession': {'default': '[autoset]'},
    }
    column_list = ('accession', 'title', 'campus_location', 'promo_location')
    can_view_details = True
    create_template = 'admin/overrides/item_edit.htm'
    edit_template = 'admin/overrides/item_edit.htm'

    def on_model_change(self, form, model, is_created):
        if (not hasattr(form, 'accession')) or form.accession.data in ('', 'auto', '[autoset]'):
            # Auto-set accession
            # TODO: Come up with a more foolproof way of doing this (what
            # if many records with smaller accession numbers are deleted?)
            accession_int = Item.objects.count() + 1
            ok = False
            for _ in range(10): # Try only 10 times
                if _check_unique_accession('%s' % accession_int):
                    ok = True
                    break
                accession_int += 1
            if ok:
                model.accession = '%s' % accession_int
            else:
                raise ValueError('Could not generate a unique accession')

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
        'accession': {'default': '[autoset]'},
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
