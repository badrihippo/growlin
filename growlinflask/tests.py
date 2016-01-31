import unittest
from models import UserGroup, User, CampusLocation, Item, BorrowPast, BorrowError, AlreadyBorrowed
import mongoengine as mongo
from mongoengine.context_managers import switch_db

class GrowlinModelTestCase(unittest.TestCase):
    def setUp(self):
        test_db = mongo.connect('testdb')

        # Groups
        self.g1 = UserGroup(name='Mars').save()
        self.g2 = UserGroup(name='Jupiter').save()

        # Users       
        self.u1 = User(name='Phobos', group=self.g1).save()
        self.u2 = User(name='Deimos', group=self.g1).save()
        self.u3 = User(name='Europa', group=self.g2).save()
        self.u4 = User(name='Ganymede', group=self.g2).save()

        # Locations
        self.l1 = CampusLocation(name='Main').save()

        # Items
        self.i1 = Item(title='Nothing', campus_location=self.l1, accession='1').save()
        self.i2 = Item(title='Something', campus_location=self.l1, accession='2').save()
        self.i3 = Item(title='This thing', campus_location=self.l1, accession='3').save()
        self.i4 = Item(title='That thing', campus_location=self.l1, accession='4').save()

    def tearDown(self):
        BorrowPast.objects().delete()
        Item.objects().delete()
        CampusLocation.objects().delete()
        User.objects().delete()
        UserGroup.objects().delete()

class BorrowTestCase(GrowlinModelTestCase):

    def test_borrow_unborrow(self):         
        assert self.i1.borrow_current is None
        assert self.i2.borrow_current is None

        # Try borrowing some stuff...
        try:
            self.u3.borrow(self.i1)
        except BorrowError: pass
        assert(self.i1.borrow_current is None)

        # Properly borrow
        self.u3.borrow(self.i1, '1')
        assert(self.i1.borrow_current.user == self.u3)
        assert(self.i1.borrow_current.user.name == 'Europa')

        # Borrow another
        self.u3.borrow(self.i2, '2')
        assert(self.i2.borrow_current.user == self.u3)

        # Try to borrow
        try:
            self.u2.borrow(self.i2, '2')
        except AlreadyBorrowed: pass
        assert (self.i1.borrow_current.user == self.u3)

        # Try to unborrow
        try:
            p = self.u3.unborrow(self.i2)
        except BorrowError: pass
        assert(self.i2.borrow_current.user == self.u3)

        # Actually unborrow
        p = self.u3.unborrow(self.i2, '2')
        assert(self.i2.borrow_current is None)
        assert(isinstance(p, BorrowPast))

        # Try again (successfully this time) to borrow
        self.u2.borrow(self.i2, '2')
        assert(self.i2.borrow_current.user == self.u2)       

    def test_current_borrow_list(self):
        # Check borrowings list
        assert(self.u1.get_current_borrowings().count() == 0)
        self.u1.borrow(self.i1, '1')
        self.u1.borrow(self.i2, '2')
        assert(self.u1.get_current_borrowings().count() == 2)

    def test_past_borrow_lists(self):
        assert(self.u1.get_past_borrowings().count() == 0)
        self.u1.borrow(self.i1, '1')
        self.u1.borrow(self.i2, '2')
        self.u1.unborrow(self.i1, '1')
        assert(self.u1.get_past_borrowings().count() == 1)
        assert(self.u1.get_past_borrowings()[0].item.title == self.i1.title)

if __name__ == '__main__':
    unittest.main()
