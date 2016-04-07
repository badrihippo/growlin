from ..app import db
import peewee

from flask.ext.login import UserMixin
from datetime import datetime

# Some custom errors.
# TODO: Move to separate file if there are many of them?
class GrowlinException(Exception): pass
class BorrowError(GrowlinException): pass
class AlreadyBorrowed(BorrowError): pass
class AccessionMismatch(BorrowError): pass

# Thanks to Nils Philippsen on StackOverflow: http://stackoverflow.com/a/2544313/1196444
class classproperty(property):
    '''
    Decorate a property so that it works like a property for the whole
    class (ie. the class itself, not the class instance).
    '''
    def __get__(self, obj, type_):
        return self.fget.__get__(None, type_)()

    def __set__(self, obj, value):
        cls = type(obj)
        return self.fset.__get__(None, cls)(value)

class ObjectManager():
    '''
    Manager to manage Growlin's peewee models using a MongoEngine-style
    syntax
    '''
    def __init__(self, model, *args, **kwargs):
        self.model = model

    def __iter__(self):
        return iter(self.model.select())

    def get(self, *args, **kwargs):
        return self.model.get(*args, **kwargs)

    def count(self, *args, **kwargs):
        return self.model.select().count(*args, **kwargs)

class BaseModel(db.Model):
    '''
    def __new__(cls, *args, **kwargs):
        cls.objects = ObjectManager()
        return cls.__new__(cls, *args, **kwargs)
    '''
    @classproperty
    @classmethod
    def objects(self):
        return ObjectManager(self)

# Admin masters

class CampusLocation(BaseModel):
    name = peewee.CharField(max_length=32, unique=True)
    # Following field can be enabled later, if required/implemented
    prevent_borrowing = peewee.BooleanField(default=False)
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class UserGroup(BaseModel):
    '''Describes Group (eg. Class) for a User to belong to'''
    name = peewee.CharField(max_length=128) # primary_key=True
    position = peewee.IntegerField(verbose_name='Display Order', default=0)
    # Can be enabled later if required/implemented
    # visible = db.BooleanField(default=True)
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}
    class Meta:
        order_by = ['position']

class UserRole(BaseModel):    
    name = peewee.CharField(max_length=16, unique=True) # primary_key=True
    # List of permissions supplied by this role
    permissions = peewee.CharField(null=True)

    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class Currency(BaseModel):
    name = peewee.CharField(max_length=32, unique=True)
    symbol = peewee.CharField(max_length=4)  
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class User(BaseModel, UserMixin):
    username = peewee.CharField(max_length=32, unique=True)
    password = peewee.CharField(max_length=512, null=True)
    # refnum = peewee.CharField(null=True)
    name = peewee.CharField(max_length=32)
    group = peewee.ForeignKeyField(UserGroup)
    email = peewee.CharField(null=True)
    # phone = peewee.CharField(max_length=16, null=True)
    # birthday = pw.DateField(null=True)
    active = peewee.BooleanField(default=True)
    @property
    def roles(self):
        return UserRoles.select().where(UserRoles.user == self)
    class Meta:
        order_by = ['name']

    def __unicode__(self):
        return '%(name)s, %(group)s' % {
            'name': self.name,
            'group': self.group.name}

    def borrow(self, item, accession=None, longterm=False):
        '''
        Marks an Item as "borrowed" by filling the borrow_current field, after
        checking for valid accession number.

        This function returns an instance of the borrowed item.
        '''
        # Check arguments
        if not isinstance(item, Item):
            raise TypeError('"item" must be an instance of Item')
        
        # Make sure item is not already borrowed
        if item.borrow_current is not None:
            raise AlreadyBorrowed('"%(title)s" is already borrowed!' %
                {'title': item.get_display_title()})

        # Check for accession number mismatch
        if (accession is not None) and (accession != item.accession):
            raise AccessionMismatch('Accession numbers do not match')
        b = BorrowCurrent(
            user=self,
            borrow_date=datetime.now(),
            item=item,
            is_longterm=longterm)
        b.save()
        return item

    # "return" is a reserved word!
    def unborrow(self, item, accession=None):
        '''
        Marks an Item as "returned" using the database models, after checking
        for valid accession number. A BorrowError is raised if either the item
        is not borrowed by that user or the accession numbers do not match.

        This function clears the borrow_current field and returns a newly created
        PastBorrowing model instance used to hold historic records.
        '''

        # Check arguments
        if not isinstance(item, Item):
            raise TypeError('"item" must be an instance of Item')
        # Refresh to get most recent record
        
        # Do user check
        if item.borrow_current is None or item.borrow_current.user != self:
            raise BorrowError('You have not borrowed that item')

        if (accession is not None) and (accession != item.accession):
            raise AccessionMismatch('Accession numbers do not match')
                
        p = BorrowPast(
            item=item,
            user=self,
            user_group=self.group.name,
            borrow_date = item.borrow_current.borrow_date,
            return_date = datetime.now()
            )
        item.borrow_current.delete_instance()
        p.save()
        return p

    def get_current_borrowings(self):
        '''
        Gets the list of books currently borrowed by the user.
        '''
        
        return (Item
            .select(Item, BorrowCurrent)
            .join(BorrowCurrent)
            .where(BorrowCurrent.user == self))
        
    def get_past_borrowings(self):
        '''
        Gets the list of records for books previously borrowed by the user.
        '''
        
        return BorrowPast.select().where(BorrowPast.user == self)

class UserRoles(BaseModel):
    '''
    Maps role to user (since MySQL has no ListFields)
    '''
    user = peewee.ForeignKeyField(User)
    role = peewee.ForeignKeyField(UserRole)
    @property
    def name(self):
        return self.role.name

class Publisher(BaseModel):
    name = peewee.CharField(max_length=128, unique=True)
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class PublishPlace(BaseModel):
    name = peewee.CharField(max_length=128, unique=True)
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class Creator(BaseModel):
    '''Author, illustrator, etc.'''
    name = peewee.CharField(max_length=128, unique=True)
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class Genre(BaseModel):
    '''Item genre'''
    name = peewee.CharField(max_length=32, unique=True) # primary_key=True
    def __unicode__(self):
        return '%s' % self.name

class ItemType(BaseModel):
    name = peewee.CharField(max_length=32, unique=True)
    prefix = peewee.CharField(max_length=1, null=True)
    icon_name = peewee.CharField(max_length=24, null=True)
    icon_color = peewee.CharField(max_length=16, null=True)

    def __unicode__(self):
        return '%s' % self.name

class Item(BaseModel):
    '''
    Holds data for items in the Accession Register. Each of these items can 
    have one or more Copies associated with it, each with its own Accession
    Number.
    '''
    item_type = peewee.ForeignKeyField(ItemType)
    accession = peewee.CharField(unique=True) # String since old values have prefix
    status = peewee.CharField(choices=(
        ('a','Available'),
        ('b', 'Borrowed'),
        ('l', 'Lost'),
        ('d', 'Discarded'),
        ('q', 'Quarantined')),
        default='a')
        
    title = peewee.CharField(max_length=128,
        help_text='Full title of book, or name of Magazine/Periodical')
    subtitle = peewee.CharField(max_length=128, null=True)
    keywords = peewee.CharField(max_length=256, null=True)
    comments = peewee.CharField(null=True)

    campus_location = peewee.ForeignKeyField(CampusLocation)
    promo_location = peewee.ForeignKeyField(CampusLocation,
        help_text='Prominent place where item is placed temporarily to attract readers',
        related_name='promo_items',
        null=True)

    # Source
    price = peewee.DecimalField(decimal_places=2, null=True)
    price_currency = peewee.ForeignKeyField(Currency, null=True)
    receipt_date = peewee.DateTimeField(default=datetime.now(), null=True) # TODO: Possible to do only date?
    source = peewee.CharField(max_length=128, null=True) # Where it came from
    
    # TODO: May be implemented later
    #display_title = peewee.CharField(max_length=256,
    #    help_text='Short version of title, for displaying in lists.\
    #    Leave blank or set to "auto" to auto-set',
    #    default='auto')
    
    def __unicode__(self):
        return '%(title)s' % {
            'title': self.title}

    def get_display_title(self):
        return self.title

    @property
    def item_class(self):
        return self.item_type.name
    @property
    def borrow_current(self):
        b = BorrowCurrent.select().where(BorrowCurrent.item == self)
        if b.exists():
            return b[0]
        else:
            return None

    class Meta:
        validate_backrefs = False

# Following is not Librarian master but has to come here for technical reasons

class BorrowCurrent(BaseModel):
    '''
    Tracks one instance of an accessed item getting borrowed.
    NOTE: In MongoEngine, this is an EmbeddedDocument
    '''
    item = peewee.ForeignKeyField(Item, related_name='current_borrow')
    user = peewee.ForeignKeyField(User)
    borrow_date = peewee.DateTimeField()
    due_date = peewee.DateTimeField(null=True)

    # TODO: Discuss if this is required
    is_longterm = peewee.BooleanField(default=False)
    def __unicode__(self):
        return '%(user)s on %(date)s' % {
            'user': self.user,
            'date': self.borrow_date}

class BookPublicationDetails():
    def __init__(self, model, *args, **kwargs):
        self.model = model
    @property
    def publisher(self):
        return self.model.publication_publisher
    @property
    def place(self):
        return self.model.publication_place
    @property
    def year(self):
        return self.model.publication_year

class BookItem(Item):
    call_no = peewee.CharField(max_length=8, null=True)

    publication_publisher = peewee.ForeignKeyField(Publisher, null=True)
    publication_place = peewee.ForeignKeyField(PublishPlace, null=True)
    publication_year = peewee.IntegerField(null=True)

    isbn = peewee.CharField(max_length=17, null=True) # TODO: Add validation

    author = peewee.ForeignKeyField(Creator, related_name='authored_items', null=True)
    editor = peewee.ForeignKeyField(Creator, related_name='edited_items', null=True)
    illustrator = peewee.ForeignKeyField(Creator, related_name='illustrated_items', null=True)

    @property
    def call_nos(self):
        return [self.call_no]

    @property
    def authors(self):
        return [self.author]
    @property
    def editors(self):
        return [self.editor]
    @property
    def illustrators(self):
        return [self.illustrator]

    # EmbeddedDocument compat
    @property
    def publication(self):
        return BookPublicationDetails(self)

    class Meta:
        db_table = 'item'

class BookCreator(Item):
    creator = peewee.ForeignKeyField(Creator)
    book_item = peewee.ForeignKeyField(BookItem)

    @property
    def name(self):
        return self.creator.name

PERIODICAL_FREQUENCY_CHOICES = (
    ('unknown', 'Unknown'),
    ('monthly', 'Monthly'),
    ('bimonthly', 'Bi-monthly'),
    ('fortnightly', 'Fortnightly'),
    ('weekly', 'Weekly'),
    ('quarterly', 'Quarterly'),
)
class PeriodicalSubscription(BaseModel):
    periodical_name = peewee.CharField(max_length=64)
    description = peewee.TextField(null=True)
    frequency = peewee.CharField(max_length=16,
        choices=PERIODICAL_FREQUENCY_CHOICES)
    current = peewee.BooleanField(default=True)
    expiry = peewee.DateTimeField(null=True)
    price = peewee.DecimalField(decimal_places=2, null=True)
    price_currency = peewee.ForeignKeyField(Currency, null=True)
    subscription_number = peewee.CharField(max_length=64, null=True)
    receipt_mode = peewee.TextField(null=True)
    comments = peewee.TextField(null=True)

    def __unicode__(self):
        return '%s' % self.periodical_name

class PeriodicalItem(Item):
    periodical_name = peewee.ForeignKeyField(PeriodicalSubscription, null=True)

    vol_no = peewee.IntegerField(verbose_name='Volume', null=True)
    vol_issue = peewee.IntegerField(verbose_name='Vol. issue', null=True)
    
    issue_no = peewee.IntegerField(verbose_name='Issue no', null=True)
    issue_date = peewee.DateTimeField(verbose_name='Issue Date', null=True)
    date_hide_day = peewee.BooleanField('Hide issue date',
        help_text='eg. "May 2015" instead of "22 May 2015"',
        default=False)

    # TODO: inserts can be added as ListField!

    def get_display_title(self, title=None, call_no=None):
        return '%(title)s,%(date)s%(month)s%(year)s: %(cover)s' % {
            'title': title,
            'date': ' %s' % ('' if self.date_hide_day else self.date.day),
            'month': '%s ' % self.date.strftime('%B'),
            'year': self.date.year,
            'cover': self.cover_content[:20]
            }

    class Meta:
        db_table = 'item'

# Convenience model to generate tables.
# Inherits from all Item models
class FullItem(BookItem, PeriodicalItem):
    class Meta:
        db_table = 'item'

# For historic records

class BorrowPast(BaseModel):
    '''
    Tracks past instances of borrowing. This model is separate from
    the Borrowing model so that information can be stored in a more
    concise way, as lookups are not going to be made as frequently as
    in the Borrowing model.
    '''
    item = peewee.ForeignKeyField(Item)
    user = peewee.ForeignKeyField(User) # Can be CharField field also?
    user_group = peewee.CharField()
    
    borrow_date = peewee.DateTimeField()
    return_date = peewee.DateTimeField()
    def __unicode__(self):
        return '%(item)s by %(user)s (%(group)s) on %(date)s' % {
            'item': self.item.title,
            'user': self.user,
            'group': self.user_group,
            'date': self.borrow_date}

def get_item_types():
    '''
    Returns a list of currenty available item types
    '''
    return [i.name for i in ItemType.select()]
