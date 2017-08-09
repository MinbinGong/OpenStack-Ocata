# Copyright 2016 - Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os

from oslo_config import cfg
from oslo_log import log as logging

from vitrage.common.constants import DatasourceAction
from vitrage.common.constants import DatasourceProperties as DSProps
from vitrage.common.constants import GraphAction
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources.static_physical import driver
from vitrage.datasources.static_physical import STATIC_PHYSICAL_DATASOURCE
from vitrage.datasources.static_physical import SWITCH
from vitrage.tests import base
from vitrage.tests.mocks import utils
from vitrage.utils import file as file_utils


LOG = logging.getLogger(__name__)


class TestStaticPhysicalDriver(base.BaseTest):

    OPTS = [
        cfg.StrOpt('transformer',
                   default='vitrage.datasources.static_physical.transformer.'
                           'StaticPhysicalTransformer'),
        cfg.StrOpt('driver',
                   default='vitrage.datasources.static_physical.driver.'
                           'StaticPhysicalDriver'),
        cfg.IntOpt('changes_interval',
                   default=30,
                   min=30,
                   help='interval between checking changes in the '
                        'configuration files of the physical topology plugin'),
        cfg.StrOpt('directory',
                   default=utils.get_resources_dir() + '/static_datasources'),
        cfg.ListOpt('entities',
                    default=[SWITCH])
    ]

    CHANGES_OPTS = [
        cfg.StrOpt('transformer',
                   default='vitrage.datasources.static_physical.transformer.'
                           'StaticPhysicalTransformer'),
        cfg.StrOpt('driver',
                   default='vitrage.datasources.static_physical.driver.'
                           'StaticPhysicalDriver'),
        cfg.IntOpt('changes_interval',
                   default=30,
                   min=30,
                   help='interval between checking changes in the '
                        'configuration files of the physical topology plugin'),
        cfg.StrOpt('directory',
                   default=utils.get_resources_dir() +
                   '/static_datasources/changes_datasources'),
    ]

    # noinspection PyAttributeOutsideInit,PyPep8Naming
    @classmethod
    def setUpClass(cls):
        cls.conf = cfg.ConfigOpts()
        cls.conf.register_opts(cls.OPTS, group=STATIC_PHYSICAL_DATASOURCE)
        cls.static_physical_driver = driver.StaticPhysicalDriver(cls.conf)

    def test_static_datasources_loader(self):
        # Setup
        total_static_datasources = \
            os.listdir(self.conf.static_physical.directory)

        # Action
        static_configs = file_utils.load_yaml_files(
            self.conf.static_physical.directory)

        # Test assertions
        # -1 is because there are 2 files and a folder in static_datasource_dir
        self.assertEqual(len(total_static_datasources) - 1,
                         len(static_configs))

    def test_get_all(self):
        # Action
        static_entities = \
            self.static_physical_driver.get_all(DatasourceAction.UPDATE)

        # Test assertions
        self.assertEqual(5, len(static_entities))

    # noinspection PyAttributeOutsideInit
    def test_get_changes(self):
        # Setup
        entities = self.static_physical_driver.get_all(DatasourceAction.UPDATE)
        self.assertEqual(5, len(entities))

        self.conf = cfg.ConfigOpts()
        self.conf.register_opts(self.CHANGES_OPTS,
                                group=STATIC_PHYSICAL_DATASOURCE)
        self.static_physical_driver.cfg = self.conf

        # Action
        changes = self.static_physical_driver.get_changes(
            GraphAction.UPDATE_ENTITY)

        # Test Assertions
        status = any(change[VProps.TYPE] == SWITCH and
                     change[VProps.ID] == '12345' for change in changes)
        self.assertEqual(False, status)

        status = any(change[VProps.TYPE] == SWITCH and
                     change[VProps.ID] == '23456' and
                     change[DSProps.EVENT_TYPE] == GraphAction.DELETE_ENTITY
                     for change in changes)
        self.assertEqual(True, status)

        status = any(change[VProps.TYPE] == SWITCH and
                     change[VProps.ID] == '34567' for change in changes)
        self.assertEqual(True, status)

        status = any(change[VProps.TYPE] == SWITCH and
                     change[VProps.ID] == '45678' for change in changes)
        self.assertEqual(True, status)
        status = any(change[VProps.TYPE] == SWITCH and
                     change[VProps.ID] == '56789' for change in changes)
        self.assertEqual(True, status)

        self.assertEqual(4, len(changes))

        # Action
        changes = self.static_physical_driver.get_changes(
            GraphAction.UPDATE_ENTITY)

        # Test Assertions
        self.assertEqual(0, len(changes))
