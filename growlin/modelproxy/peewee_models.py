from ..app import db
import peewee

from flask.ext.login import UserMixin
from datetime import datetime

# Some custom errors.
# TODO: Move to separate file if there are many of them?
class GrowlinException(Exception): pass
class BorrowError(GrowlinException): pass
class AlreadyBorrowed(BorrowError): pass

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
    name = peewee.CharField(max_length=32)
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

class UserRole(BaseModel):    
    name = peewee.CharField(max_length=16) # primary_key=True
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
    name = peewee.CharField(max_length=24)
    group = peewee.ForeignKeyField(UserGroup)
    email = peewee.CharField(null=True)
    # phone = peewee.CharField(max_length=16, null=True)
    # birthday = pw.DateField(null=True)
    active = peewee.BooleanField(default=True)
    @property
    def roles(self):
        return UserRoles.select().where(UserRoles.user == self)

    def __unicode__(self):
        return '%(name)s, %(group)s' % {
            'name': self.name,
            'group': self.group.name}

    def borrow(self, item, accession=None, longterm=False, interactive=False):
        '''
        Marks an Item as "borrowed" by filling the borrow_current field, after
        checking for valid accession number. Setting the "interactive" flag
        will cause the function to open a prompt for dynamic input of the
        accession number.

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
        if interactive and accession is None:
            accession = int(raw_input('Enter accession for "%(title)s": ' %
                {'title': item.get_display_title()}))
        if accession != item.accession:
            raise BorrowError('Accession numbers do not match')
       
        b = item.borrow_current = BorrowCurrent(
                user=self,
                borrow_date = datetime.now(),
                is_longterm = longterm)
        # TODO: Race condition protection?
        b.save()
        return b

    # "return" is a reserved word!
    def unborrow(self, item, accession=None, interactive=False):
        '''
        Marks an Item as "returned" using the database models, after checking
        for valid accession number. A BorrowError is raised if either the item
        is not borrowed by that user or the accession numbers do not match.
        Setting the "interactive" flag will cause the function to open a prompt
        for dynamic input of the accession number.

        This function clears the borrow_current field and returns a newly created
        PastBorrowing model instance used to hold historic records.
        '''

        # Check arguments
        if not isinstance(item, Item):
            raise TypeError('"item" must be an instance of Item')
        # Refresh to get most recent record
        item.reload()
        
        # Do user check
        if item.borrow_current is None or item.borrow_current.user != self:
            raise BorrowError('You have not borrowed that item')

        if interactive and accession is None:
            accession = int(raw_input('Enter accession for "%(title)s": ' %
                {'title': item.title}))
        if accession != item.accession:
            raise BorrowError('Accession numbers do not match')
                
        p = BorrowPast(
            item=item,
            user=self,
            user_group=self.group.name,
            borrow_date = item.borrow_current.borrow_date,
            return_date = datetime.now()
            )
        del(item.borrow_current)
        p.save()
        item.save()
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
    name = peewee.CharField(max_length=32) # primary_key=True
    def __unicode__(self):
        return '%s' % self.name

class ItemType(BaseModel):
    item_type = peewee.CharField(max_length=32)

    def __unicode__(self):
        return '%s' % self.item_type

class Item(BaseModel):
    '''
    Holds data for items in the Accession Register. Each of these items can 
    have one or more Copies associated with it, each with its own Accession
    Number.
    '''
    item_type = peewee.ForeignKeyField(ItemType)
    accession = peewee.CharField() # String since old values have prefix
    status = peewee.CharField(choices=(
        ('a','Available'),
        ('b', 'Borrowed'),
        ('l', 'Lost'),
        ('d', 'Discarded'),
        ('q', 'Quarantined')))
        
    title = peewee.CharField(max_length=128,
        help_text='Full title of book, or name of Magazine/Periodical')
    subtitle = peewee.CharField(max_length=128, null=True)
    keywords = peewee.CharField(max_length=256)
    comments = peewee.CharField(null=True)

    campus_location = peewee.ForeignKeyField(CampusLocation)
    promo_location = peewee.ForeignKeyField(CampusLocation,
        help_text='Prominent place where item is placed temporarily to attract readers',
        related_name='promo_items',
        null=True)

    # Source
    price = peewee.DecimalField(decimal_places=2)
    price_currency = peewee.ForeignKeyField(Currency)
    receipt_date = peewee.DateTimeField() # TODO: Possible to do only date?
    source = peewee.CharField(max_length=64) # Where it came from
    
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
        return self.item_type.item_type

# Following is not Librarian master but has to come here for technical reasons

class BorrowCurrent(BaseModel):
    '''
    Tracks one instance of an accessed item getting borrowed.
    NOTE: In MongoEngine, this is an EmbeddedDocument
    '''
    item = peewee.ForeignKeyField(Item, related_name='borrow_current')
    user = peewee.ForeignKeyField(User)
    borrow_date = peewee.DateTimeField()
    due_date = peewee.DateTimeField()

    # TODO: Discuss if this is required
    is_longterm = peewee.BooleanField(default=False)
    def __unicode__(self):
        return '%(user)s on %(date)s' % {
            'user': self.user,
            'date': self.borrow_date}

'''
class BookPublicationDetails(db.EmbeddedDocument):
    publisher = peewee.ForeignKeyField(Publisher)
    place = peewee.ForeignKeyField(PublishPlace)
    year = peewee.IntegerField(max_value=9999) # TODO: Make this more year-friendly

class BookItem(Item):
    call_no = peewee.ListField(db.CharField(max_length=8))
    publication = peewee.EmbeddedDocumentField(BookPublicationDetails)
    isbn = peewee.CharField(max_length=17) # TODO: Add validation
    authors = peewee.ListField(db.ForeignKeyField(Creator))
    editor = peewee.ListField(db.ForeignKeyField(Creator))
    illustrator = peewee.ListField(db.ForeignKeyField(Creator))
'''

class PeriodicalSubscription(BaseModel):
    periodical_name = peewee.CharField(max_length=64)
    # More fields can be added here...

'''
class PeriodicalItem(Item):
    periodical_name = peewee.ForeignKeyField(PeriodicalSubscription)

    vol_no = peewee.IntegerField(verbose_name='Volume')
    vol_issue = peewee.IntegerField(verbose_name='Vol. issue')
    
    issue_no = peewee.IntegerField(verbose_name='Issue no')
    issue_date = peewee.DateTimeField(verbose_name='Issue Date')
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
'''

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
            'acc': self.accession,
            'user': self.user,
            'group': self.group,
            'date': self.borrow_date}
