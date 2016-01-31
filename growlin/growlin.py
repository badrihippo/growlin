from .app import app
from .auth import *
from .admin import admin
from .models import *
from .views import *

if __name__ == '__main__':
    app.run()
