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

import pecan

from oslo_log import log
from pecan.core import abort
from pecan import rest
from vitrage.api.policy import enforce
# noinspection PyProtectedMember
from vitrage.i18n import _LI


LOG = log.getLogger(__name__)


class ResourcesController(rest.RestController):

    @pecan.expose()
    def _lookup(self, id_, *remainder):
        LOG.info(_LI('got lookup %s') % id_)
        return ResourceController(id_), remainder

    @pecan.expose('json')
    def index(self, resource_type=None):
        enforce('list resources', pecan.request.headers,
                pecan.request.enforcer, {})

        LOG.info(_LI('received list resources with filter %s') % resource_type)

        try:
            return self.get_resources(resource_type)
        except Exception as e:
            LOG.exception('failed to get resources %s', e)
            abort(404, str(e))

    @staticmethod
    def get_resources(resource_type):
        # todo(eyalb1) need a mock for this
        return [{'None': None}]


class ResourceController(rest.RestController):

    def __init__(self, id_):
        self.id = id_

    @pecan.expose('json')
    def get(self):
        enforce('get resource', pecan.request.headers,
                pecan.request.enforcer, {})

        LOG.info(_LI('received get resource with id %s') % self.id)
        try:
            return self.get_resource(self.id)
        except Exception as e:
            LOG.exception('failed to get resource %s', e)
            abort(404, str(e))

    @staticmethod
    def get_resource(id_):
        # todo(eyalb1) need a mock for this
        return {'None': None}
