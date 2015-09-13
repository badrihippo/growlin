import models
import mongoengine as mongo
from mongoengine.context_managers import switch_db
test_db_name = 'testdb'
test_db = mongo.connect(test_db_name, alias='test_db')

def test_borrow_unborrow():
    with switch_db(models.UserGroup, 'test_db') as UserGroup, switch_db(models.User, 'test_db') as User, switch_db(models.CampusLocation, 'test_db') as CampusLocation,  switch_db(models.Item, 'test_db') as Item, switch_db(models.BorrowPast, 'test_db') as BorrowPast:

        g = UserGroup(name='Jupiter').save()
        u1 = User(name='Europa', group=g).save()
        u2 = User(name='Ganymede', group=g).save()
        l = CampusLocation(name='Main').save()
        i1 = Item(title='Nothing', campus_location=l, accession='0').save()
        i2 = Item(title='Something', campus_location=l, accession='1').save()

        assert i1.borrow_current is None
        assert i2.borrow_current is None

        # Try borrowing some stuff...
        try:
            u1.borrow(i1)
        except models.BorrowError: pass
        assert(i1.borrow_current is None)

        # Properly borrow
        u1.borrow(i1, '0')
        assert(i1.borrow_current.user == u1)
        assert(i1.borrow_current.user.name == 'Europa')

        # Borrow another
        u1.borrow(i2, '1')
        assert(i2.borrow_current.user == u1)

        # Check borrowings list
        assert(u1.get_current_borrowings().count() == 2)
        assert(u2.get_current_borrowings().count() == 0)

        # Try to borrow
        try:
            u2.borrow(i2, '1')
        except models.AlreadyBorrowed: pass
        assert (i1.borrow_current.user == u1)

        # Try to unborrow
        try:
            p = u1.unborrow(i2)
        except models.BorrowError: pass
        assert(i2.borrow_current.user == u1)

        # Actually unborrow
        p = u1.unborrow(i2, '1')
        assert(i2.borrow_current is None)
        assert(isinstance(p, BorrowPast))

        # Try again (successfully this time) to borrow
        u2.borrow(i2, '1')
        assert(i2.borrow_current.user == u2)

        # Cleanup...

        UserGroup.objects().delete()
        User.objects().delete()
        CampusLocation.objects().delete()
        Item.objects().delete()
        BorrowPast.objects().delete()
        
