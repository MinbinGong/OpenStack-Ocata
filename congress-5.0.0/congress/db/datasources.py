# Copyright (c) 2012 OpenStack Foundation.
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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json

import sqlalchemy as sa
from sqlalchemy.orm import exc as db_exc

from congress.db import api as db
from congress.db import db_ds_table_data as table_data
from congress.db import model_base


class Datasource(model_base.BASE, model_base.HasId):
    __tablename__ = 'datasources'

    name = sa.Column(sa.String(255), unique=True)
    driver = sa.Column(sa.String(255))
    config = sa.Column(sa.Text(), nullable=False)
    description = sa.Column(sa.Text(), nullable=True)
    enabled = sa.Column(sa.Boolean, default=True)

    def __init__(self, id_, name, driver, config, description,
                 enabled=True):
        self.id = id_
        self.name = name
        self.driver = driver
        self.config = json.dumps(config)
        self.description = description
        self.enabled = enabled


def add_datasource(id_, name, driver, config, description,
                   enabled, session=None):
    session = session or db.get_session()
    with session.begin(subtransactions=True):
        datasource = Datasource(
            id_=id_,
            name=name,
            driver=driver,
            config=config,
            description=description,
            enabled=enabled)
        session.add(datasource)
    return datasource


def delete_datasource(id_, session=None):
    session = session or db.get_session()
    return session.query(Datasource).filter(
        Datasource.id == id_).delete()


def delete_datasource_with_data(id_, session=None):
    session = session or db.get_session()
    with session.begin(subtransactions=True):
        deleted = delete_datasource(id_, session)
        table_data.delete_ds_table_data(id_, session=session)
    return deleted


def get_datasource_name(name_or_id, session=None):
    session = session or db.get_session()
    datasource_obj = get_datasource(name_or_id, session)
    if datasource_obj is not None:
        return datasource_obj.name
    return name_or_id


def get_datasource(name_or_id, session=None):
    db_object = (get_datasource_by_name(name_or_id, session) or
                 get_datasource_by_id(name_or_id, session))

    return db_object


def get_datasource_by_id(id_, session=None):
    session = session or db.get_session()
    try:
        return (session.query(Datasource).
                filter(Datasource.id == id_).
                one())
    except db_exc.NoResultFound:
        pass


def get_datasource_by_name(name, session=None):
    session = session or db.get_session()
    try:
        return (session.query(Datasource).
                filter(Datasource.name == name).
                one())
    except db_exc.NoResultFound:
        pass


def get_datasources(session=None, deleted=False):
    session = session or db.get_session()
    return (session.query(Datasource).
            all())
