# Copyright 2015 - Alcatel-Lucent
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

from oslo_utils import timeutils
# noinspection PyPackageRequirements
from oslotest import base
import sys


class BaseTest(base.BaseTestCase):
    """Test case base class for all unit tests."""

    def assert_list_equal(self, l1, l2):
        if tuple(sys.version_info)[0:2] < (2, 7):
            # for python 2.6 compatibility
            self.assertEqual(l1, l2)
        else:
            super(BaseTest, self).assertListEqual(l1, l2)

    def assert_dict_equal(self, d1, d2, message):
        if tuple(sys.version_info)[0:2] < (2, 7):
            # for python 2.6 compatibility
            self.assertEqual(d1, d2)
        else:
            super(BaseTest, self).assertDictEqual(d1, d2, message)

    def assert_timestamp_equal(self, first, second, msg=None):
        """Checks that two timestamps are equals.

        This relies on assertAlmostEqual to avoid rounding problem, and only
        checks up the first microsecond values.

        """
        return self.assertAlmostEqual(timeutils.delta_seconds(first, second),
                                      0.0,
                                      places=5, msg=msg)

    def assert_is_empty(self, obj):
        try:
            if len(obj) != 0:
                self.fail("%s is not empty" % type(obj))
        except (TypeError, AttributeError):
            self.fail("%s doesn't have length" % type(obj))

    def assert_is_not_empty(self, obj):
        try:
            if len(obj) == 0:
                self.fail("%s is empty" % type(obj))
        except (TypeError, AttributeError):
            self.fail("%s doesn't have length" % type(obj))

    @staticmethod
    def path_get(project_file=None):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                            '..',
                                            '..',
                                            )
                               )
        if project_file:
            return os.path.join(root, project_file)
        else:
            return root

    def setUp(self):
        super(BaseTest, self).setUp()
