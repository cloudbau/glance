#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Glance Management Utility
"""

from __future__ import print_function

# FIXME(sirp): When we have glance-admin we can consider merging this into it
# Perhaps for consistency with Nova, we would then rename glance-admin ->
# glance-manage (or the other way around)

import os
import sys

# If ../glance/__init__.py exists, add ../ to Python search path, so that
# it will override what happens to be installed in /usr/(local/)lib/python...
possible_topdir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                   os.pardir,
                                   os.pardir))
if os.path.exists(os.path.join(possible_topdir, 'glance', '__init__.py')):
    sys.path.insert(0, possible_topdir)

from oslo.config import cfg

from glance.common import config
from glance.common import exception
import glance.db.sqlalchemy.api
import glance.db.sqlalchemy.migration
from glance.openstack.common import log

CONF = cfg.CONF


def do_db_version():
    """Print database's current migration level"""
    print(glance.db.sqlalchemy.migration.db_version())


def do_upgrade():
    """Upgrade the database's migration level"""
    glance.db.sqlalchemy.migration.upgrade(CONF.command.version)


def do_downgrade():
    """Downgrade the database's migration level"""
    glance.db.sqlalchemy.migration.downgrade(CONF.command.version)


def do_version_control():
    """Place a database under migration control"""
    glance.db.sqlalchemy.migration.version_control(CONF.command.version)


def do_db_sync():
    """
    Place a database under migration control and upgrade,
    creating first if necessary.
    """
    glance.db.sqlalchemy.migration.db_sync(CONF.command.version,
                                           CONF.command.current_version)


def add_command_parsers(subparsers):
    parser = subparsers.add_parser('db_version')
    parser.set_defaults(func=do_db_version)

    parser = subparsers.add_parser('upgrade')
    parser.set_defaults(func=do_upgrade)
    parser.add_argument('version', nargs='?')

    parser = subparsers.add_parser('downgrade')
    parser.set_defaults(func=do_downgrade)
    parser.add_argument('version')

    parser = subparsers.add_parser('version_control')
    parser.set_defaults(func=do_version_control)
    parser.add_argument('version', nargs='?')

    parser = subparsers.add_parser('db_sync')
    parser.set_defaults(func=do_db_sync)
    parser.add_argument('version', nargs='?')
    parser.add_argument('current_version', nargs='?')


command_opt = cfg.SubCommandOpt('command',
                                title='Commands',
                                help='Available commands',
                                handler=add_command_parsers)


def main():
    CONF.register_cli_opt(command_opt)
    try:
        # We load the glance-registry config section because
        # sql_connection is only part of the glance registry.
        glance.db.sqlalchemy.api.add_cli_options()

        cfg_files = cfg.find_config_files(project='glance',
                                          prog='glance-registry')
        cfg_files.extend(cfg.find_config_files(project='glance',
                                               prog='glance-api'))
        config.parse_args(default_config_files=cfg_files,
                          usage="%(prog)s [options] <cmd>")
        log.setup('glance')
    except RuntimeError as e:
        sys.exit("ERROR: %s" % e)

    try:
        CONF.command.func()
    except exception.GlanceException as e:
        sys.exit("ERROR: %s" % e)


if __name__ == '__main__':
    main()
