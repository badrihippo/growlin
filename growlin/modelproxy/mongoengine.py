from ..app import db

from flask.ext.login import UserMixin
from datetime import datetime

# Some custom errors.
# TODO: Move to separate file if there are many of them?
class GrowlinException(Exception): pass
class BorrowError(GrowlinException): pass
class AlreadyBorrowed(BorrowError): pass

# Admin masters

class CampusLocation(db.Document):
    name = db.StringField(max_length=128, primary_key=True)
    # Following field can be enabled later, if required/implemented
    prevent_borrowing = db.BooleanField(default=False)
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class UserGroup(db.Document):
    '''Describes Group (eg. Class) for a User to belong to'''
    name = db.StringField(max_length=128, primary_key=True)
    position = db.IntField(verbose_name='Display order', default=0)
    # Can be enabled later if required/implemented
    # visible = db.BooleanField(default=True)
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class UserRole(db.Document):    
    name = db.StringField(max_length=16, primary_key=True)    
    # List of permissions supplied by this role
    permissions = db.ListField(db.StringField(max_length=32))
    

    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class Currency(db.Document):
    name = db.StringField(max_length=32, unique=True)
    symbol = db.StringField(max_length=4)  
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

# Librarian Masters

class User(db.Document, UserMixin):
    username = db.StringField(max_length=32, unique=True)
    password = db.StringField(max_length=512)
    # refnum = db.StringField(null=True)
    name = db.StringField(max_length=24, required=True)
    group = db.ReferenceField(UserGroup, required=True)
    email = db.EmailField()
    # phone = db.StringField(max_length=16, null=True)
    # birthday = pw.DateField(null=True)
    active = db.BooleanField(default=True)
    roles = db.ListField(db.ReferenceField(UserRole))

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
        
        return Item.objects(borrow_current__user=self)
        
    def get_past_borrowings(self):
        '''
        Gets the list of records for books previously borrowed by the user.
        '''
        
        return BorrowPast.objects(user=self)

class Publisher(db.Document):
    name = db.StringField(max_length=128, unique=True)
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class PublishPlace(db.Document):
    name = db.StringField(max_length=128, unique=True)
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class Creator(db.Document):
    '''Author, illustrator, etc.'''
    name = db.StringField(max_length=128, unique=True)
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class Genre(db.Document):
    '''Item genre'''
    name = db.StringField(max_length=32, primary_key=True)
    def __unicode__(self):
        return '%s' % self.name

# Following is not Librarian master but has to come here for technical reasons
class BorrowCurrent(db.EmbeddedDocument):
    '''
    Tracks one instance of an accessed item getting borrowed.
    '''
    user = db.ReferenceField(User, required=True)
    borrow_date = db.DateTimeField(required=True)
    due_date = db.DateTimeField()

    # TODO: Discuss if this is required
    is_longterm = db.BooleanField(default=False)
    def __unicode__(self):
        return '%(user)s on %(date)s' % {
            'user': self.user,
            'date': self.borrow_date}

class Item(db.Document):
    '''
    Holds data for items in the Accession Register. Each of these items can 
    have one or more Copies associated with it, each with its own Accession
    Number.
    '''
    accession = db.StringField(required=True) # String since old values have prefix
    status = db.StringField(choices=(
        ('a','Available'),
        ('b', 'Borrowed'),
        ('l', 'Lost'),
        ('d', 'Discarded'),
        ('q', 'Quarantined')))
        
    title = db.StringField(max_length=128,
        help_text='Full title of book, or name of Magazine/Periodical', required=True)
    subtitle = db.StringField(max_length=128)
    keywords = db.ListField(db.StringField(max_length=16))
    comments = db.StringField()

    campus_location = db.ReferenceField(CampusLocation, required=True)
    promo_location = db.ReferenceField(CampusLocation,
        help_text='Prominent place where item is placed temporarily to attract readers')

    # Source
    price = db.DecimalField(precision=2)
    price_currency = db.ReferenceField(Currency)
    receipt_date = db.DateTimeField() # TODO: Possible to do only date?
    source = db.StringField(max_length=64) # Where it came from

    borrow_current = db.EmbeddedDocumentField(BorrowCurrent)
    
    # TODO: May be implemented later
    #display_title = db.StringField(max_length=256,
    #    help_text='Short version of title, for displaying in lists.\
    #    Leave blank or set to "auto" to auto-set',
    #    default='auto')
    
    def __unicode__(self):
        return '%(title)s' % {
            'title': self.title}

    def get_display_title(self):
        return self.title

    meta = {'allow_inheritance': True}

class BookPublicationDetails(db.EmbeddedDocument):
    publisher = db.ReferenceField(Publisher)
    place = db.ReferenceField(PublishPlace)
    year = db.IntField(max_value=9999) # TODO: Make this more year-friendly

class BookItem(Item):
    call_no = db.ListField(db.StringField(max_length=8))
    publication = db.EmbeddedDocumentField(BookPublicationDetails)
    isbn = db.StringField(max_length=17) # TODO: Add validation
    authors = db.ListField(db.ReferenceField(Creator))
    editor = db.ListField(db.ReferenceField(Creator))
    illustrator = db.ListField(db.ReferenceField(Creator))

class PeriodicalSubscription(db.Document):
    periodical_name = db.StringField(max_length=64)
    # More fields can be added here...

class PeriodicalItem(Item):
    periodical_name = db.ReferenceField(PeriodicalSubscription)

    vol_no = db.IntField(verbose_name='Volume')
    vol_issue = db.IntField(verbose_name='Vol. issue')
    
    issue_no = db.IntField(verbose_name='Issue no')
    issue_date = db.DateTimeField(verbose_name='Issue Date')
    date_hide_day = db.BooleanField('Hide issue date',
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

# For historic records

class BorrowPast(db.Document):
    '''
    Tracks past instances of borrowing. This model is separate from
    the Borrowing model so that information can be stored in a more
    concise way, as lookups are not going to be made as frequently as
    in the Borrowing model.
    '''
    item = db.ReferenceField(Item)
    user = db.ReferenceField(User) # Can be StringField field also?
    user_group = db.StringField()
    
    borrow_date = db.DateTimeField()
    return_date = db.DateTimeField()
    def __unicode__(self):
        return '%(item)s by %(user)s (%(group)s) on %(date)s' % {
            'acc': self.accession,
            'user': self.user,
            'group': self.group,
            'date': self.borrow_date}

def create_tables():
    '''WARNING: Deprecated function. Do not use!'''
    print 'Mongo does not use tables!'

# TODO: HIPPO: Continue from here!
def create_test_data():
    print 'Generating test data...'
    models = (Group, Role, User, UserRoles, PublishPlace, Publisher, Currency, Author, Location, Publication, Copy, Borrowing, PastBorrowing) + tuple(all_pubtypes.union(all_pubcopies))
    for Model in models:
        print 'Resetting table: ', Model
        Model.drop_table(fail_silently=True)
        Model.create_table(fail_silently=True)

    print 'Inserting test data: ',

    print '[users]',
    g = Group.create(name='Earth')
    User.create(name='Moon', password='pass', group=g)

    g = Group.create(name='Mars')
    User.create(name='Phobos', group=g)
    User.create(name='Deimos', group=g)

    g = Group.create(name='Jupiter')
    User.create(name='Io', group=g)
    User.create(name='Europa', group=g)
    User.create(name='Ganymede', group=g)
    User.create(name='Callisto', group=g)

    g = Group.create(name='Saturn')
    User.create(name='Titan', group=g)
    User.create(name='Enceladus', group=g)
    User.create(name='Tethys', group=g)
    User.create(name='Mimas', group=g)
    User.create(name='Dione', group=g)

    print '[roles]',

    r = Role.create(name='admin', description='access the admin interface')
    u = UserRoles.create(role=r, user=User.get(username='europa'))
    u = UserRoles.create(role=r, user=User.get(username='moon'))

    print '[locations]',

    loc_main = Location.create(name='Main')

    print '[publications]',
    p = Publication.create(title='The Slippery Seals',
        comments='The first book in the SNAP booklet series',
        keywords='snap, seals, wildlife')
    c1 = Copy.create(item=p,
        accession=1,
        location=loc_main,
        source='Stolen from the store!',
        receipt_date=datetime.now())
    c2 = Copy.create(item=p,
        accession=2,
        location=loc_main,
        source='A gift from the valley',
        receipt_date=datetime.now())
    p = Publication.create(title='The Ferocious Felids',
        comments='The second book in the SNAP booklet series',
        keywords='snap, cats, lions, tigers, leopards, wildlife')
    c3 = Copy.create(item=p,
        accession=3,
        location=loc_main,
        source='Bought at Ascraeus Mons',
        receipt_date=datetime.now())

    print '[borrowings]',
    e = User.get(username='europa')
    e.borrow(c1,1)
    e.unborrow(c1,1)
    e.borrow(c2,2)
    e.borrow(c3,3)
    e.unborrow(c3,3)
    e.borrow(c3,3)

    print '...done.'
