Growlin
=======

Library mangement program for the CFL [Open Library](http://library.cfl.in/about/)

About the Open Library
======================

[Centre For Learning](http://cfl.in) (CFL) is a school near Bangalore, India, which has this thing called the [Open Library](http://library.cfl.in/about/). Basically, **anyone can come in and borrow books** (the librarian makes accounts for all the students, staff and guests) and enter their borrowings in the library's computer. To make sure that the book is actually coming back, users have to enter the book's accession number, which will be written inside the book. The idea is that everyone takes responsibility for the books, instead of having one librarian doing all the managing.

The program currently being used for the library management is called Merlin, and it is being used in several schools as well as CFL.

Now, the Merlin application code is very old and buggy, so I've been asked to make a new one.
But, since this is the first proper program I'm making, the end result may be a program that's very *new* and buggy. 

I'm putting this program on GitHub in the hope that other people may decide to help and improve the code. And maybe if it gets enough attention more people will start setting up Open Libraries...

The old software was called "Merlin", hence I decided to name the new one after my dog, Growlin.

The Growlin Interface
=====================

Right now I'm planning to make two interfaces for Growlin: one is the user's interface where they manage their borrowings, and the other is the admin interface where the librarian can add new books, etc.

Project layout
==============

The project is going to be run on Django. For developing, the database is going to be SQLite, but in the actual one it'll be replaced with MySQL or something. The Django project is in the growlinserv folder, in case we need the rest of the space for other files.
