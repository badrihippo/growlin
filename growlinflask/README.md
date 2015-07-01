Growlin: Flask version
======================

This folder contains an experimental alternative to the Django app, written
in Flask. I'm still experimenting with Flask at the moment, but after I've
tried it out for a while I may begin developing this instead of the main Django
app. Flask seems to be better suited to Growlin, because of its minimal design
which will make it more suitable for packaging as a desktop app.

To run the server, `cd` to this (growlinflask) directory and run
`python growlin.py`.

This app currently makes use of [Flask](http://flask.pocoo.org),
[Flask-Admin](http://flask-admin.org),
[Flask_Security](http://pythonhosted.org/Flask-Security/) and
the [peewee](http://peewee.readthedocs.org) database ORM.
