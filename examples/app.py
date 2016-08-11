# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.


"""Minimal Flask application example for development.

Create the database and run the example development server:

.. code-block:: console

   $ cd examples
   $ mkdir instance
   $ export FLASK_APP=app.py
   $ flask db init
   $ flask db create
   $ flask run
"""

from __future__ import absolute_import, print_function

from flask import Flask
from flask_admin.contrib.sqla import ModelView
from flask_babelex import Babel
from flask_login import LoginManager
from invenio_db import InvenioDB, db

from invenio_admin import InvenioAdmin
from invenio_admin.views import protected_adminview_factory

# Create Flask application
app = Flask(__name__)
Babel(app)
admin_app = InvenioAdmin(app)
LoginManager(app)
InvenioDB(app)
app.config.update(
    SECRET_KEY="CHANGE_ME",
)


class TestModel(db.Model):
    """Simple model with just one column."""

    id = db.Column(db.Integer, primary_key=True)
    """Id of the model."""


class TestModelView(ModelView):
    """ModelView of the TestModel."""

    pass

protected_view = protected_adminview_factory(TestModelView)
admin_app.admin.add_view(protected_view(TestModel, db.session))
