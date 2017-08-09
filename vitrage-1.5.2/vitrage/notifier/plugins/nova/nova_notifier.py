# Copyright 2016 - Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from oslo_log import log as logging

from vitrage.common.constants import NotifierEventTypes
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources import NOVA_HOST_DATASOURCE
from vitrage.notifier.plugins.base import NotifierBase
from vitrage import os_clients

LOG = logging.getLogger(__name__)


class NovaNotifier(NotifierBase):

    @staticmethod
    def get_notifier_name():
        return 'nova'

    def __init__(self, conf):
        super(NovaNotifier, self).__init__(conf)
        self.client = os_clients.nova_client(conf)

    def process_event(self, data, event_type):
        if data and data.get(VProps.TYPE) == NOVA_HOST_DATASOURCE:
            if event_type == NotifierEventTypes.ACTIVATE_MARK_DOWN_EVENT:
                self._mark_host_down(data.get(VProps.ID), True)
            elif event_type == NotifierEventTypes.DEACTIVATE_MARK_DOWN_EVENT:
                self._mark_host_down(data.get(VProps.ID), False)

    def _mark_host_down(self, host_id, is_down):
        try:
            LOG.info('Nova services.force_down - host id: %s, is_down: %s',
                     str(host_id), str(is_down))
            response = self.client.services.force_down(
                host_id, 'nova-compute', is_down)
            LOG.info('RESPONSE %s', str(response))
        except Exception as e:
            LOG.exception('Failed to services.force_down - %s', e)
