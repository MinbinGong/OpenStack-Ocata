# Copyright 2016 - Nokia Corporation
# Copyright 2014 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from vitrage.tests.functional import api


VERSIONS_RESPONSE = {u'versions': [{u'id': u'v1.0',
                                    u'links': [
                                        {u'href': u'http://localhost/v1/',
                                         u'rel': u'self'}],
                                    u'status': u'CURRENT',
                                    u'updated': u'2015-11-29'}]}


class TestVersions(api.FunctionalTest):
    def test_versions(self):
        data = self.get_json('/')
        self.assertEqual(VERSIONS_RESPONSE, data)
