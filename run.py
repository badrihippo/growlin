import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'flask-admin-material'))

from growlin import *

if __name__ == '__main__':
    app.run()
