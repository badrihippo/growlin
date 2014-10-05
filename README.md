Growlin
=======

Library mangement program for the CFL Open Library

About the Open Library
======================

Centre For Learning (CFL) is a school near Bangalore, India, which has this thing called the Open Library. Basically, **anyone can come in and borrow books** (the librarian makes accounts for all the students, staff and guests) and enter their borrowings in the library's computer. To make sure that the book is actually coming back, users have to enter the book's accession number, which will be written inside the book. The idea is that everyone takes responsibility for the books, instead of having one librarian doing all the managing.

Now, the program currently being used for managing the library is very old and buggy. So I've been asked to make a new one.
This is the first proper program I'm making, so the end result may be a program that is very *new* and buggy. 

I'm putting this program on GitHub in the hope that other people may decide to help and improve the code. And maybe if it gets enough attention more people will start setting up Open Libraries...

The old software was called "Merlin", hence I decided to name the new one after my dog, Growlin.

The Growlin Interface
=====================

Right now I'm planning to make two interfaces for Growlin: one is the user's interface where they manage their borrowings, and the other is the admin interface where the librarian can add new books, etc.

Currently I'm planning to use the `peewee` library for the database, so that it can support multiple engines, and Python's `Gtk` library for the interface. The library computer runs Windows but I'm running Ubuntu, so I'll try to make the program as portable as possible.
