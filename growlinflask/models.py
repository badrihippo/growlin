import peewee as pw
from flask.ext.login import UserMixin
#from flask.ext.security import UserMixin, RoleMixin
from wtfpeewee.orm import model_form
from playhouse import gfk
from datetime import datetime

# Some custom errors.
# TODO: Move to separate file if there are many of them?
class GrowlinException(Exception): pass
class BorrowError(GrowlinException): pass

db = pw.SqliteDatabase('growlin.db')

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

    def get(self, *args, **kwargs):
        self.model.get(*args, **kwargs)

class BaseModel(pw.Model):
    '''
    def __new__(cls, *args, **kwargs):
        cls.objects = ObjectManager()
        return cls.__new__(cls, *args, **kwargs)
    '''
    @classproperty
    @classmethod
    def objects(self):
        return ObjectManager(self)
    class Meta:
        database = db

class PublishPlace(BaseModel):
    name = pw.CharField(max_length=512, unique=True)
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class Publisher(BaseModel):
    name = pw.CharField(max_length=256)
    address = pw.TextField(null=True)
    imprint_of = pw.ForeignKeyField('self', null=True)
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class Currency(BaseModel):
    name = pw.CharField(max_length=32, unique=True)
    symbol = pw.CharField(max_length=4)
    conversion_factor = pw.FloatField(default=1)    
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}


class Author(BaseModel):
    #id = pw.IntegerField()
    name = pw.CharField(max_length=128)
    is_pseudonym = pw.BooleanField(default=False)
    author_sort = pw.CharField(max_length=128, default='auto', index=True )
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}
    def save(self, *args, **kwargs):
        # Set the slug if field is blank
        if self.author_sort == 'auto' or not self.author_sort:
            split_name = self.name.split()
            self.author_sort = split_name[-1] + ', ' + reduce(
                lambda x,y: x + ' ' + y, split_name[:-1])
        # Do the real save
        super(Author, self).save(*args, **kwargs)

class Location(BaseModel):
    name = pw.CharField(max_length=256, unique=True)
    prevent_borrowing = pw.BooleanField(default=False)
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class Publication(BaseModel):
    '''
    Holds data for items in the Accession Register. Each of these items can 
    have one or more Copies associated with it, each with its own Accession
    Number.
    '''
    title = pw.CharField(max_length=512,
        help_text='Full title of book, or name of Magazine/Periodical')
    display_title = pw.CharField(max_length=256,
        help_text='Short version of title, for displaying in lists.\
        Leave blank or set to "auto" to auto-set',
        default='auto')
    pubtype = pw.CharField(null=True)
    pubdata_id = pw.IntegerField(null=True)
    pubdata = gfk.GFKField('pubtype', 'pubdata_id')

    #current_borrower = ForeignKeyField('User', null=True)
    identifier = pw.CharField(max_length=256, null=True)
    call_no = pw.CharField(max_length=8, default='000')
    keywords = pw.CharField(max_length=1024, null=True)
    comments = pw.TextField(null=True)
    
    def __unicode__(self):
        return '%(display_title)s - %(call_no)s' % {
            'call_no': self.call_no, 
            'display_title': self.display_title}
    def save(self, *args, **kwargs):
        # Set the slug if field is blank
        if self.display_title == 'auto' or not self.display_title:
            if hasattr(self.pubdata, 'get_display_title'):
                self.display_title = self.pubdata.get_display_title(self.title, self.call_no)
                if not self.display_title:
                    self.display_title = self.title
            else:
                self.display_title = self.title
                
        # Do the real save
        super(Publication, self).save(*args, **kwargs)


class Copy(BaseModel):
    '''
    Entry for one accessed item. Other metadata is linked using other
    classes like Book, Periodical, etc.; this model holds only the info
    common to all types of accession
    '''
    accession = pw.IntegerField(unique=True)
    item = pw.ForeignKeyField(Publication, related_name='copies')
    location = pw.ForeignKeyField(Location)

    copydata_type = pw.CharField(null=True)
    copydata_id = pw.CharField(null=True)
    copydata = gfk.GFKField('copydata_type', 'copydata_id')

    #Source
    price = pw.FloatField(default=0, null=True)
    price_currency = pw.ForeignKeyField(Currency, null=True)
    receipt_date = pw.DateField(null=True)
    source = pw.CharField(max_length=512, null=True)
    class Meta:
        verbose_name = 'Copy'
        verbose_name_plural = 'Copies'
    
    # TODO: comments, keywords
    def __unicode__(self):
        return '%(accession)s - %(display_title)s' % {
            'accession': self.accession, 
            'display_title': self.item.display_title}
    class Meta:
        verbose_name = 'Copy'
        verbose_name_plural = 'Copies'

all_pubtypes = set()
all_pubcopies = set()

class BaseBasePubType(gfk.BaseModel):
    def __new__(cls, name, bases, attrs):
        cls = super(BaseBasePubType, cls).__new__(cls, name, bases, attrs)
        cls.publication = gfk.ReverseGFK(Publication, 'pubtype', 'pubdata_id')
        return cls
        
class BasePubType(pw.with_metaclass(BaseBasePubType, pw.Model)):
    '''
    For storing extra type-related information for a Publication.
    Models subclassing this one will be added to the available options
    for a Publication to store extra information.

    TODO: Right now, submodels are added to playhouse.gfk's default
    `all_models` set. This needs to be changed so that the are added to
    a special `all_pubtypes` set instead.
    '''
    
    class Meta:
        database = db


class BaseBaseCopyType(gfk.BaseModel):
    def __new__(cls, name, bases, attrs):
        cls = super(BaseBaseCopyType, cls).__new__(cls, name, bases, attrs)
        cls.copy = gfk.ReverseGFK(Copy, 'copydata_type', 'copydata_id')
        return cls

class BaseCopyType(pw.with_metaclass(BaseBaseCopyType, pw.Model)):
    '''
    For storing extra type-related information for a Copy of a publication.
    Models subclassing this one will be added to the available options
    for a Copy to store extra information.

    TODO: Right now, submodels are added to playhouse.gfk's default
    `all_models` set. This needs to be changed so that the are added to
    a special `all_pubcopies` set instead.
    '''
    
    class Meta:
        database = db

'''
class Person(User):
    \'''Describes info for one particular user\'''
    # id = pw.PrimaryKeyField
    name = pw.CharField(max_length=256)
    group = pw.ForeignKeyField('Group', db_constraint=False)
    #password = pw.CharField(max_length=128)
    #last_login = pw.DateTimeField(null=True)
    #creation_date = pw.DateTimeField(null=True)
    #email = pw.CharField(max_length=128, null=True)
    phone = pw.CharField(max_length=16, blank=True, null=True)
    refnum = pw.CharField(max_length=16, null=True)
    birthday = pw.DateField(blank=True, null=True)
    def __unicode__(self):
        return self.name
'''

class Group(BaseModel):
    '''Describes Group (eg. Class) for a User to belong to'''
    position = pw.IntegerField(verbose_name='Ordering position', default=0)
    name = pw.CharField(max_length=128, index=True)
    visible = pw.BooleanField(default=True)
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class User(BaseModel, UserMixin):
    username = pw.CharField(32, unique=True)
    password = pw.CharField(512, null=True)
    group = pw.ForeignKeyField(Group, related_name='users')
    refnum = pw.CharField(null=True)
    name = pw.CharField(64)
    email = pw.CharField(64, null=True)
    phone = pw.CharField(max_length=16, null=True)
    birthday = pw.DateField(null=True)
    active = pw.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        # Set the username if field is blank
        if self.username == 'auto' or not self.username:
            self.username = self.name.replace(' ', '').lower()
        # Set default email; used till we figure out how to override default
        # login field used by Flask-Security
        if not self.email:
            self.email = '%s@growlin' % self.name.replace(' ', '').lower()
        # Do the real save
        super(User, self).save(*args, **kwargs)

    def __unicode__(self):
        return '%(group)s - %(refnum)s%(name)s (%(username)s)' % {
            'name': self.name,
            'refnum': self.refnum + ' - ' if self.refnum else '',
            'username': self.username,
            'group': self.group.name}

    def borrow(self, copy, accession=None, longterm=False, interactive=False):
        '''
        Marks a Copy as "borrowed" using the Borrowed database model, after
        checking for valid accession number. Setting the "interactive" flag
        will cause the function to open a prompt for dynamic input of the
        accession number.

        This function returns the newly created Borrowing instance
        '''
        
        if interactive and accession is None:
            accession = int(raw_input('Enter accession for "%(title)s": ' %
                {'title': copy.item.title}))
        if accession != copy.accession:
            raise BorrowError('Accession numbers do not match.')
        # Reborrowing will stop because of unique constraint on
        # Borrowing.accession field
        try:
            b = Borrowing.create(
                user=self,
                copy=copy,
                group=self.group,
                borrow_date = datetime.now(),
                is_longterm = longterm)
            return b
        except pw.IntegrityError, e:
            if e.message == 'UNIQUE constraint failed: borrowing.copy_id':
                raise BorrowError('Item is already borrowed!')
            else:
                raise e

    # "return" is a reserved word!
    def unborrow(self, copy_or_borrow, accession=None, interactive=False):
        '''
        Marks a Copy as "returned" using the database models, after checking
        for valid accession number. You can give either the actual Borrowing
        instance or the Copy object that needs to be returned. Setting the
        "interactive" flag will cause  the function to open a prompt for
        dynamic input of the accession number.

        This function deletes the Borrowing model and returns a newly created
        PastBorrowing model instance used to hold historic records. 
        '''

        if type(copy_or_borrow) == Copy:
            try:
                b = Borrowing.get(
                    Borrowing.copy == copy_or_borrow,
                    Borrowing.user == self)
            except Borrowing.DoesNotExist:
                raise BorrowError('You have not borrowed that item!')
        elif type(copy_or_borrow) == Borrowing:
            if copy_or_borrow.user != self:
                raise BorrowError('That item is not borrowed by you!')
            else:
                b = copy_or_borrow
        else:
            raise ValueError('copy_or_borrow must be either a Copy or Borrowing instance')

        if interactive and accession is None:
            accession = int(raw_input('Enter accession for "%(title)s": ' %
                {'title': b.copy.item.title}))
        if accession != b.copy.accession:
            raise BorrowError('Accession numbers do not match.')
                
        p = PastBorrowing.create(
            user=self,
            accession=b.copy.accession,
            group=self.group,
            borrow_date = b.borrow_date,
            return_date = datetime.now()
            )
        b.delete_instance()
        return p

    def get_current_borrowings(self):
        '''
        Gets the list of records for books currently borrowed by the user.
        '''

        b = Borrowing.select().where(Borrowing.user == self)
        c = Copy.select().join(Publication)
        return pw.prefetch(b,c).select()

class Role(BaseModel):
    name = pw.CharField(unique=True)
    description = pw.TextField(null=True)

    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class UserRoles(BaseModel):
    # Because peewee does not come with built-in many-to-many
    # relationships, we need this intermediary class to link
    # user to roles.
    user = pw.ForeignKeyField(User, related_name='roles')
    role = pw.ForeignKeyField(Role, related_name='users')
    name = property(lambda self: self.role.name)
    description = property(lambda self: self.role.description)

    
class Borrowing(BaseModel):
    '''
    Tracks one instance of an accessed item getting borrowed.
    This model may also store redundant information such as title, in
    order to make lookups faster.
    '''
    copy = pw.ForeignKeyField(Copy, unique=True)
    user = pw.ForeignKeyField(User)
    group = pw.ForeignKeyField(Group)
    borrow_date = pw.DateTimeField()
    renew_times = pw.IntegerField(default=0)
    is_longterm = pw.BooleanField(default=False)
    def __unicode__(self):
        return '%(acc)s by %(user)s (%(group)s) on %(date)s' % {
            'acc': self.copy,
            'user': self.user,
            'group': self.group,
            'date': self.borrow_date}
            
class PastBorrowing(BaseModel):
    '''
    Tracks past instances of borrowing. This model is separate from
    the Borrowing model so that information can be stored in a more
    concise way, as lookups are not going to be made as frequently as
    in the Borrowing model.
    '''
    accession = pw.IntegerField() # Non-enforced FK to Accession
    user = pw.ForeignKeyField(User)
    group = pw.ForeignKeyField(Group)
    borrow_date = pw.DateTimeField()
    return_date = pw.DateTimeField()
    def __unicode__(self):
        return '%(acc)s by %(user)s (%(group)s) on %(date)s' % {
            'acc': self.accession,
            'user': self.user,
            'group': self.group,
            'date': self.borrow_date}

# Extra Pub/Copy data models defined below

class PubPeriodical(BasePubType):
    cover_content = pw.CharField(verbose_name='Cover content', 
        max_length=512,
        help_text='Cover article/image/story (for magazines, etc.)',
        null=True)
    issue = pw.IntegerField(verbose_name='Issue no', null=True)
    vol_no = pw.IntegerField(verbose_name='Volume', null=True)
    vol_issue = pw.IntegerField(verbose_name='Vol. issue', null=True)
    date = pw.DateField(verbose_name='Issue Date', null=True)
    date_hide_day = pw.BooleanField('Hide issue date',
        help_text='eg. "May 2015" instead of "22 May 2015"',
        default=False)

    def get_display_title(self, title=None, call_no=None):
        return '%(title)s,%(date)s%(month)s%(year)s: %(cover)s' % {
            'title': title,
            'date': ' %s' % ('' if self.date_hide_day else self.date.day),
            'month': '%s ' % self.date.strftime('%B'),
            'year': self.date.year,
            'cover': self.cover_content[:20]
            }
    class Meta:
        verbose_name = 'Periodical details'
all_pubtypes.add(PubPeriodical)

class CopyBook(BaseCopyType):
    pub_name = pw.ForeignKeyField(Publisher, 
        #db_constraint=False, 
        verbose_name='Publisher',
        null=True)
    pub_place = pw.ForeignKeyField(PublishPlace,
        verbose_name = 'Place of Publication',
        null=True)
    pub_date = pw.DateField(null=True,
        verbose_name = 'Date of Publication')
    class Meta:
        verbose_name = 'Book copy details'
all_pubcopies.add(CopyBook)


def create_tables():
    db.connect()
    db.create_tables([PublishPlace, Publisher, Currency])
    db.create_tables([Author, Location,])
    db.create_tables([Publication, Copy])
    db.create_tables([Group, User, Role, UserRoles])
    db.create_tables([Borrowing, PastBorrowing])

    # Extra pub data
    db.create_tables(gfk.all_models)

def create_test_data():
    print 'Generating test data...'
    models = (Group, Role, User, UserRoles, PublishPlace, Publisher, Currency, Author, Location, Publication, Copy, Borrowing, PastBorrowing) + tuple(all_pubtypes.union(all_pubcopies))
    for Model in models:
        print 'Resetting table: ', Model
        Model.drop_table(fail_silently=True)
        Model.create_table(fail_silently=True)

    print 'Inserting test data: ',

    print '[groups]',
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
