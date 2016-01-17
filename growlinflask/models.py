import mongoengine as mongo
from flask.ext.login import UserMixin
from wtfpeewee.orm import model_form
from datetime import datetime

# Some custom errors.
# TODO: Move to separate file if there are many of them?
class GrowlinException(Exception): pass
class BorrowError(GrowlinException): pass
class AlreadyBorrowed(BorrowError): pass

db = mongo.connect('growlindb')

# Admin masters

class CampusLocation(mongo.Document):
    name = mongo.StringField(max_length=128, primary_key=True)
    # Following field can be enabled later, if required/implemented
    # prevent_borrowing = mongo.BooleanField(default=False)
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class UserGroup(mongo.Document):
    '''Describes Group (eg. Class) for a User to belong to'''
    name = mongo.StringField(max_length=128, primary_key=True)
    position = mongo.IntField(verbose_name='Ordering position', default=0)
    # Can be enabled later if required/implemented
    # visible = mongo.BooleanField(default=True)
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class UserRole(mongo.Document):    
    name = mongo.StringField(max_length=16, primary_key=True)    
    # List of permissions supplied by this role
    permissions = mongo.ListField(mongo.StringField(max_length=32))
    

    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class Currency(mongo.Document):
    name = mongo.StringField(max_length=32, unique=True)
    symbol = mongo.StringField(max_length=4)  
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

# Librarian Masters

class User(mongo.Document, UserMixin):
    # username = mongo.StringField(32, unique=True)
    # password = mongo.StringField(512, null=True)
    # refnum = mongo.StringField(null=True)
    name = mongo.StringField(max_length=24, required=True)
    group = mongo.ReferenceField(UserGroup, required=True)
    email = mongo.EmailField()
    # phone = mongo.StringField(max_length=16, null=True)
    # birthday = pw.DateField(null=True)
    active = mongo.BooleanField(default=True)
    roles = mongo.ListField(mongo.ReferenceField(UserRole))

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
        if item.borrow_current.user != self:
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

class Publisher(mongo.Document):
    name = mongo.StringField(max_length=128, unique=True)
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class PublishPlace(mongo.Document):
    name = mongo.StringField(max_length=128, unique=True)
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class Creator(mongo.Document):
    '''Author, illustrator, etc.'''
    name = mongo.StringField(max_length=128, unique=True)
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

# Following is not Librarian master but has to come here for technical reasons
class BorrowCurrent(mongo.EmbeddedDocument):
    '''
    Tracks one instance of an accessed item getting borrowed.
    '''
    user = mongo.ReferenceField(User, required=True)
    borrow_date = mongo.DateTimeField(required=True)
    due_date = mongo.DateTimeField()

    # TODO: Discuss if this is required
    is_longterm = mongo.BooleanField(default=False)
    def __unicode__(self):
        return '%(user)s on %(date)s' % {
            'user': self.user,
            'date': self.borrow_date}

class Item(mongo.Document):
    '''
    Holds data for items in the Accession Register. Each of these items can 
    have one or more Copies associated with it, each with its own Accession
    Number.
    '''
    accession = mongo.StringField(required=True) # String since old values have prefix
    status = mongo.StringField(choices=(
        ('a','Available'),
        ('b', 'Borrowed'),
        ('l', 'Lost'),
        ('d', 'Discarded'),
        ('q', 'Quarantined')))
        
    title = mongo.StringField(max_length=128,
        help_text='Full title of book, or name of Magazine/Periodical', required=True)
    subtitle = mongo.StringField(max_length=128)
    keywords = mongo.ListField(mongo.StringField(max_length=16))
    comments = mongo.StringField()

    campus_location = mongo.ReferenceField(CampusLocation, required=True)
    promo_location = mongo.ReferenceField(CampusLocation,
        help_text='Prominent place where item is placed temporarily to attract readers')

    # Source
    price = mongo.DecimalField(precision=2)
    price_currency = mongo.ReferenceField(Currency)
    receipt_date = mongo.DateTimeField() # TODO: Possible to do only date?
    source = mongo.StringField(max_length=64) # Where it came from

    borrow_current = mongo.EmbeddedDocumentField(BorrowCurrent)
    
    # TODO: May be implemented later
    #display_title = mongo.StringField(max_length=256,
    #    help_text='Short version of title, for displaying in lists.\
    #    Leave blank or set to "auto" to auto-set',
    #    default='auto')
    
    def __unicode__(self):
        return '%(title)s' % {
            'title': self.title}

    def get_display_title(self):
        return self.title

    meta = {'allow_inheritance': True}

class BookPublicationDetails(mongo.EmbeddedDocument):
    publisher = mongo.ReferenceField(Publisher)
    place = mongo.ReferenceField(PublishPlace)
    year = mongo.IntField(max_value=9999) # TODO: Make this more year-friendly

class BookItem(Item):
    call_no = mongo.ListField(mongo.StringField(max_length=8))
    publication = mongo.EmbeddedDocumentField(BookPublicationDetails)
    isbn = mongo.StringField(max_length=17) # TODO: Add validation
    authors = mongo.ListField(mongo.ReferenceField(Creator))
    editor = mongo.ListField(mongo.ReferenceField(Creator))
    illustrator = mongo.ListField(mongo.ReferenceField(Creator))

class PeriodicalSubscription(mongo.Document):
    periodical_name = mongo.StringField(max_length=64)
    # More fields can be added here...

class PeriodicalItem(Item):
    periodical_name = mongo.ReferenceField(PeriodicalSubscription)

    vol_no = mongo.IntField(verbose_name='Volume')
    vol_issue = mongo.IntField(verbose_name='Vol. issue')
    
    issue_no = mongo.IntField(verbose_name='Issue no')
    issue_date = mongo.DateTimeField(verbose_name='Issue Date')
    date_hide_day = mongo.BooleanField('Hide issue date',
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

class BorrowPast(mongo.Document):
    '''
    Tracks past instances of borrowing. This model is separate from
    the Borrowing model so that information can be stored in a more
    concise way, as lookups are not going to be made as frequently as
    in the Borrowing model.
    '''
    item = mongo.ReferenceField(Item)
    user = mongo.ReferenceField(User) # Can be StringField field also?
    user_group = mongo.StringField()
    
    borrow_date = mongo.DateTimeField()
    return_date = mongo.DateTimeField()
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
