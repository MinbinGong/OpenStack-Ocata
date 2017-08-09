# Copyright 2017 - Nokia
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

from datetime import datetime
from oslo_config import cfg
from oslo_log import log as logging

from vitrage.common.constants import DatasourceProperties as DSProps
from vitrage.common.constants import EventProperties as EventProps
from vitrage.common.constants import UpdateMethod
from vitrage.datasources.doctor import DOCTOR_DATASOURCE
from vitrage.datasources.doctor.properties import DoctorDetails
from vitrage.datasources.doctor.properties import DoctorProperties \
    as DoctorProps
from vitrage.datasources.doctor.properties import DoctorStatus
from vitrage.datasources.doctor.transformer import DoctorTransformer
from vitrage.datasources.nova.host import NOVA_HOST_DATASOURCE
from vitrage.datasources.nova.host.transformer import HostTransformer
from vitrage.tests.mocks import mock_transformer
from vitrage.tests.unit.datasources.test_alarm_transformer_base import \
    BaseAlarmTransformerTest

LOG = logging.getLogger(__name__)


# noinspection PyProtectedMember
class DoctorTransformerTest(BaseAlarmTransformerTest):

    OPTS = [
        cfg.StrOpt('update_method',
                   default=UpdateMethod.PUSH),
    ]

    # noinspection PyAttributeOutsideInit,PyPep8Naming
    @classmethod
    def setUpClass(cls):
        cls.transformers = {}
        cls.conf = cfg.ConfigOpts()
        cls.conf.register_opts(cls.OPTS, group=DOCTOR_DATASOURCE)
        cls.conf.register_opts(cls.OPTS, group=NOVA_HOST_DATASOURCE)
        cls.transformers[DOCTOR_DATASOURCE] = \
            DoctorTransformer(cls.transformers, cls.conf)
        cls.transformers[NOVA_HOST_DATASOURCE] = \
            HostTransformer(cls.transformers, cls.conf)

    def test_create_update_entity_vertex(self):
        # Test setup
        time1 = datetime.now().isoformat()
        host1 = 'host1'
        event = self._generate_event(time1, host1, DoctorStatus.DOWN)
        self.assertIsNotNone(event)

        # Test action
        transformer = self.transformers[DOCTOR_DATASOURCE]
        wrapper = transformer.transform(event)

        # Test assertions
        self._validate_vertex_props(wrapper.vertex, event)

        # Validate the neighbors: only one valid host neighbor
        self._validate_host_neighbor(wrapper,
                                     transformer._create_entity_key(event),
                                     host1)

        # Validate the expected action on the graph - update or delete
        self._validate_graph_action(wrapper)

        # Create an event with status 'UP'
        time2 = datetime.now().isoformat()
        host2 = 'host2'
        event = self._generate_event(time2, host2, DoctorStatus.UP)
        self.assertIsNotNone(event)

        # Test action
        transformer = self.transformers[DOCTOR_DATASOURCE]
        wrapper = transformer.transform(event)

        # Test assertions
        self._validate_vertex_props(wrapper.vertex, event)
        self._validate_host_neighbor(wrapper,
                                     transformer._create_entity_key(event),
                                     host2)
        self._validate_graph_action(wrapper)

    def _validate_vertex_props(self, vertex, event):
        self._validate_alarm_vertex_props(vertex,
                                          event[EventProps.TYPE],
                                          DOCTOR_DATASOURCE,
                                          event[DSProps.SAMPLE_DATE])

    @staticmethod
    def _generate_event(time, hostname, status):
        details = {}
        if hostname:
            details[DoctorDetails.HOSTNAME] = hostname
        if status:
            details[DoctorDetails.STATUS] = status

        update_vals = {EventProps.DETAILS: details}
        if time:
            update_vals[EventProps.TIME] = time
            update_vals[DoctorProps.UPDATE_TIME] = time

        generators = mock_transformer.simple_doctor_alarm_generators(
            update_vals=update_vals)

        return mock_transformer.generate_random_events_list(generators)[0]

    def _is_erroneous(self, vertex):
        return vertex[DoctorDetails.STATUS] == DoctorStatus.DOWN
