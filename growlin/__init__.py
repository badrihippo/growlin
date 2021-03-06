import os
import sys

# Add flask-admin-material, which is a submodule of this repo
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'../flask-admin-material'))


from .app import app
from .auth import *
from .admin import admin
from .models import *
from .views import *
from .util.prettyprint import pretty_date
app.jinja_env.globals.update(pretty_date=pretty_date)

if __name__ == '__main__':
    app.run()
