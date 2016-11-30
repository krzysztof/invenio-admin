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

"""Invenio-Admin Flask extension."""

from __future__ import absolute_import, print_function

import pkg_resources
from flask_admin import Admin, AdminIndexView
from invenio_db import db
from werkzeug import import_string

from . import config
from .views import protected_adminview_factory


class _AdminState(object):
    """State for Invenio-Admin."""

    def __init__(self, app, admin, permission_factory, view_class_factory):
        """Initialize state.

        :param app: The Flask application.
        :param admin: The Flask-Admin application.
        :param permission_factory: The permission factory to restrict access.
        :param view_class_factory: The view class factory to initialize them.
        """
        # Create admin instance.
        self.app = app
        self.admin = admin
        self.permission_factory = permission_factory
        self.view_class_factory = view_class_factory

    def register_view(self, view_class, *args, **kwargs):
        """Register an admin view on this admin instance.

        :param view_class: The view class name passed to the view factory.
        :param model_class: The model class name.
        :param session: The session handler. If not specified, ``db.session``
            will be used. (Default: ``None``)
        """
        view_class = self.view_class_factory(view_class)
        session = kwargs.pop('session') if 'session' in kwargs else None
        # TODO: Backwards compatibility with old signature:
        # register_view(self, view_class, model_class, session=None, **kwargs)
        # We assume that there can be only one extra positional argument,
        # at which point we register the ModelView, otherwise we register a
        # custom admin view.
        assert len(args) <= 1, \
            "Method accepts either one or two positional arguments"
        if args:
            model_class = args[0]
            self.admin.add_view(
                view_class(model_class, session or db.session, **kwargs))
        else:
            self.admin.add_view(view_class(**kwargs))

    def load_entry_point_group(self, entry_point_group):
        """Load administration interface from entry point group."""
        for ep in pkg_resources.iter_entry_points(group=entry_point_group):

            admin_ep = dict(ep.load())
            m, mv, v = (k in admin_ep for k in ('model', 'modelview', 'view'))
            assert (m and mv and not v) or (not m and not mv and v), \
                "Admin entrypoint dictionary must contain either " \
                "'view' OR 'model' and 'modelview' keys."

            if m and mv:
                self.register_view(admin_ep.pop('modelview'),
                                   admin_ep.pop('model'),
                                   **admin_ep)
            else:  # v
                self.register_view(admin_ep.pop('view'), **admin_ep)


class InvenioAdmin(object):
    """Invenio-Admin extension.

    :param app: Flask application.
    :param entry_point_group: Name of entry point group to load views/models
        from.
    :param permission_factory: Default permission factory to use when
        protecting admin view.
    :param viewcls_factory: Factory for creating admin view classes on the
        fly. Used to protect admin views with authentication and authorization.
    :param indeview_cls: Admin index view class.
    """

    def __init__(self, app=None, **kwargs):
        """Invenio-Admin extension initialization.

        :param app: The Flask application. (Default: ``None``)
        """
        if app:
            self._state = self.init_app(app, **kwargs)

    def init_app(self,
                 app,
                 entry_point_group='invenio_admin.views',
                 permission_factory=None,
                 view_class_factory=protected_adminview_factory,
                 index_view_class=AdminIndexView,
                 **kwargs):
        """Flask application initialization.

        :param app: The Flask application.
        :param entry_point_group: The entry point group to load extensions.
            (Default: ``'invenio_admin.views'``)
        :param permission_factory: The permission factory to restrict access.
            (Default:
            :class:`invenio_admin.permissions.admin_permission_factory`)
        :param index_view_class: Specify administrative interface index page.
            (Default: :class:`flask_admin.base.AdminIndexView`)
        """
        self.init_config(app)

        default_permission_factory = app.config['ADMIN_PERMISSION_FACTORY']
        permission_factory = permission_factory or \
            import_string(default_permission_factory)

        # Create administration app.

        admin = Admin(
            app,
            name=app.config['ADMIN_APPNAME'],
            template_mode=kwargs.get('template_mode', 'bootstrap3'),
            index_view=view_class_factory(index_view_class)(),
        )

        @app.before_first_request
        def lazy_base_template():
            """Initialize admin base template lazily."""
            base_template = app.config.get('ADMIN_BASE_TEMPLATE')
            if base_template:
                admin.base_template = base_template

        # Create admin state
        state = _AdminState(app, admin, permission_factory, view_class_factory)
        if entry_point_group:
            state.load_entry_point_group(entry_point_group)

        app.extensions['invenio-admin'] = state
        return state

    @staticmethod
    def init_config(app):
        """Initialize configuration.

        :param app: The Flask application.
        """
        # Set default configuration
        for k in dir(config):
            if k.startswith('ADMIN_'):
                app.config.setdefault(k, getattr(config, k))

    def __getattr__(self, name):
        """Proxy to state object."""
        return getattr(self._state, name, None)
