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

# noinspection PyPackageRequirements
import mock
import webtest

from vitrage.api import app
from vitrage.tests.functional.api.v1 import FunctionalTest


class TestAuthentications(FunctionalTest):
    def _make_app(self):
        file_name = self.path_get('etc/vitrage/api-paste.ini')
        self.conf.set_override("paste_config", file_name, "api")
        # We need the other call to prepare_service in app.py to return the
        # same tweaked conf object.
        with mock.patch('vitrage.service.prepare_service') as ps:
            ps.return_value = self.conf
            return webtest.TestApp(app.load_app(conf=self.conf))

    def test_not_authenticated(self):
        resp = self.post_json('/topology/', params=None, expect_errors=True)
        self.assertEqual(401, resp.status_int)
