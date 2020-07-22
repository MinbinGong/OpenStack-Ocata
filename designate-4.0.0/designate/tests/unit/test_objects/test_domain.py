# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Federico Ceratto <federico.ceratto@hpe.com>
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

import unittest

from oslo_log import log as logging
import oslotest.base
import testtools

from designate import exceptions
from designate import objects

LOG = logging.getLogger(__name__)


def create_test_zone():
    return objects.Zone(
        name='www.example.org.',
        email='foo@example.com',
    )


class zoneTest(oslotest.base.BaseTestCase):

    def test_init(self):
        zone = create_test_zone()
        self.assertEqual('www.example.org.', zone.name)

    def test_mains_none(self):
        zone = objects.Zone()
        with testtools.ExpectedException(exceptions.RelationNotLoaded):
            self.assertIsNone(zone.mains)

    def test_mains(self):
        zone = objects.Zone(
            mains=objects.ZoneMainList.from_list([
                {'host': '1.0.0.0', 'port': 53}
            ])
        )
        self.assertEqual(
            [{'host': '1.0.0.0', 'port': 53}], zone.mains.to_list())

    def test_mains_2(self):
        zone = objects.Zone(
            mains=objects.ZoneMainList.from_list([
                {'host': '1.0.0.0'},
                {'host': '2.0.0.0'}
            ])
        )
        self.assertEqual(2, len(zone.mains))

    def test_get_main_by_ip(self):
        zone = objects.Zone(
            mains=objects.ZoneMainList.from_list([
                {'host': '1.0.0.0', 'port': 53},
                {'host': '2.0.0.0', 'port': 53}
            ])
        )
        m = zone.get_main_by_ip('2.0.0.0').to_data()

        self.assertEqual('2.0.0.0:53', m)

    @unittest.expectedFailure  # bug: zone.mains is not iterable
    def test_get_main_by_ip_none(self):
        zone = objects.Zone()
        m = zone.get_main_by_ip('2.0.0.0')
        self.assertFalse(m)

    def test_validate(self):
        zone = create_test_zone()
        zone.validate()

    def test_validate_invalid_secondary(self):
        zone = objects.Zone(
            type='SECONDARY',
        )
        with testtools.ExpectedException(exceptions.InvalidObject):
            zone.validate()

    def test_validate_primary_with_mains(self):
        mains = objects.ZoneMainList()
        mains.append(objects.ZoneMain.from_data("10.0.0.1:53"))
        zone = objects.Zone(
            name='example.com.',
            type='PRIMARY',
            email="foo@example.com",
            mains=mains
        )
        with testtools.ExpectedException(exceptions.InvalidObject):
            zone.validate()

    def test_validate_primary_no_email(self):
        mains = objects.ZoneMainList()
        mains.append(objects.ZoneMain.from_data("10.0.0.1:53"))
        zone = objects.Zone(
            name='example.com.',
            type='PRIMARY',
        )
        with testtools.ExpectedException(exceptions.InvalidObject):
            zone.validate()

    def test_validate_secondary_with_email(self):
        mains = objects.ZoneMainList()
        mains.append(objects.ZoneMain.from_data("10.0.0.1:53"))
        zone = objects.Zone(
            name='example.com.',
            type='SECONDARY',
            email="foo@example.com",
            mains=mains
        )
        with testtools.ExpectedException(exceptions.InvalidObject):
            zone.validate()

    def test_validate_secondary_with_ttl(self):
        mains = objects.ZoneMainList()
        mains.append(objects.ZoneMain.from_data("10.0.0.1:53"))
        zone = objects.Zone(
            name='example.com.',
            type='SECONDARY',
            ttl=600,
            mains=mains
        )
        with testtools.ExpectedException(exceptions.InvalidObject):
            zone.validate()

    def test_validate_secondary_with_mains_empty_list(self):
        mains = objects.ZoneMainList()
        zone = objects.Zone(
            name='example.com.',
            type='SECONDARY',
            mains=mains
        )
        with testtools.ExpectedException(exceptions.InvalidObject):
            zone.validate()

    def test_validate_secondary_with_mains_none(self):
        zone = objects.Zone(
            name='example.com.',
            type='SECONDARY',
            mains=None
        )
        with testtools.ExpectedException(exceptions.InvalidObject):
            zone.validate()
