import peewee as pw
from playhouse.shortcuts import ManyToManyField
from flask.ext.security import UserMixin, RoleMixin

db = pw.SqliteDatabase('growlin.db')

class BaseModel(pw.Model):
    class Meta:
        database = db

class PublishPlace(BaseModel):
    place = pw.CharField(max_length=512, primary_key=True)
    def __unicode__(self):
        return '%(place)s' % {'place': self.place}

class Publisher(BaseModel):
    name = pw.CharField(max_length=256, primary_key=True)
    address = pw.TextField(null=True)
    imprint_of = pw.ForeignKeyField('self', null=True)
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}

class Currency(BaseModel):
    name = pw.CharField(max_length=32, primary_key=True)
    conversion_factor = pw.FloatField(default=1)    
    def __unicode__(self):
        return '%(name)s' % {'name': self.name}


class Author(BaseModel):
    #id = pw.IntegerField()
    name = pw.CharField(max_length=128)
    is_pseudonym = pw.BooleanField(default=False)
    author_sort = pw.CharField(max_length=128, default='auto')
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
    loc_name = pw.CharField(max_length=256, primary_key=True)
    prevent_borrowing = pw.BooleanField(default=False)
    def __unicode__(self):
        return '%(name)s' % {'name': self.loc_name}
        
class PublicationType(BaseModel):
    '''Type of Publication: display settings may change based on type'''
    itype = pw.CharField(primary_key=True)

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
        Set to "auto" to auto-set (recommended for periodicals)',
        default='auto')
    itype = pw.ForeignKeyField(PublicationType, verbose_name='Item type')
    mag_cover = pw.CharField(verbose_name='Cover content', 
        max_length=512,
        help_text='Cover article/image/story (for magazines, etc.)',
        null=True)
    mag_issue = pw.IntegerField(verbose_name='Issue no', null=True)
    mag_vol_no = pw.IntegerField(verbose_name='Volume', null=True)
    mag_issue_no = pw.IntegerField(verbose_name='Vol. issue', null=True)
    mag_date = pw.DateField(verbose_name='Issue Date', null=True)
    mag_date_show_day = pw.BooleanField('Hide issue date',
        help_text='eg. "May 2015" instead of "22 May 2015"',
        default=False)
    author = ManyToManyField(Author)
    location = pw.ForeignKeyField(Location)
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
            if self.itype == 'mag':
                self.display_title = '%(title)s,%(date)s%(month)s%(year)s: %(cover)s' % {
                    'title': self.title,
                    'date': ' %s' % (self.mag_date.day if self.mag_date_show_day else ''),
                    'month': '%s ' % self.mag_date.strftime('%B'),
                    'year': self.mag_date.year,
                    'cover': self.mag_cover[:20]
                    }
            else:
                self.display_title = '%(title)s' % {
                    'title': self.title
                    }
        # Do the real save
        super(Publication, self).save(*args, **kwargs)
        
class Copy(BaseModel):
    '''
    Entry for one accessed item. Other metadata is linked using other
    classes like Book, Periodical, etc.; this model holds only the info
    common to all types of accession
    '''
    accession = pw.IntegerField(primary_key=True)
    item = pw.ForeignKeyField(Publication)
    
    pub_name = pw.ForeignKeyField(Publisher, 
        #db_constraint=False, 
        verbose_name='Publisher',
        null=True)
    pub_place = pw.ForeignKeyField(PublishPlace,
        verbose_name = 'Place of Publication',
        null=True)
    pub_date = pw.DateField(null=True,
        verbose_name = 'Date of Publication')
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
    name = pw.CharField(max_length=128, primary_key=True)
    visible = pw.BooleanField(default=True)
    def __unicode__(self):
        return self.name

class User(BaseModel, UserMixin):
    refnum = pw.CharField(null=True)
    username = pw.CharField(32, unique=True)
    password = pw.CharField(512, null=True)
    group = pw.ForeignKeyField(Group)
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
    
class Role(BaseModel, RoleMixin):
    name = pw.CharField(unique=True)
    description = pw.TextField(null=True)

class UserRoles(BaseModel):
    # Because peewee does not come with built-in many-to-many
    # relationships, we need this intermediary class to link
    # user to roles.
    user = pw.ForeignKeyField(User, related_name='roles')
    role = pw.ForeignKeyField(Role, related_name='users')
    name = property(lambda self: self.role.name)
    description = property(lambda self: self.role.description)

    
class Borrowing(BaseModel):
    '''Tracks one instance of an accessed item getting borrowed'''
    accession = pw.IntegerField() # FK to Accession
    #user = pw.ForeignKeyField(Person, db_constraint=False)
    group = pw.ForeignKeyField(Group)
    borrow_date = pw.DateTimeField()
    renew_times = pw.IntegerField(default=0)
    is_returned = pw.BooleanField(default=False)
    is_longterm = pw.BooleanField(default=False)
    return_date = pw.DateTimeField(null=True)
    def __unicode__(self):
        return '%(acc)s by %(user)s (%(group)s) on %(date)s' % {
            'acc': self.accession,
            'user': self.user,
            'group': self.group,
            'date': self.borrow_date}

def create_tables():
    db.connect()
    db.create_tables([User, Relationship, Message])

