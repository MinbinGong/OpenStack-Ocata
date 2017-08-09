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

from oslo_config import cfg
from oslo_log import log as logging

from six.moves import queue
from vitrage.common.constants import DatasourceAction
from vitrage.common.constants import DatasourceProperties as DSProps
from vitrage.common.constants import EdgeProperties as EProps
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources.nova.host import NOVA_HOST_DATASOURCE
from vitrage.evaluator.scenario_evaluator import ScenarioEvaluator
from vitrage.evaluator.scenario_repository import ScenarioRepository
from vitrage.tests.functional.base import \
    TestFunctionalBase
import vitrage.tests.mocks.mock_driver as mock_driver
from vitrage.tests.mocks import utils

LOG = logging.getLogger(__name__)

_TARGET_HOST = 'host-2'
_NAGIOS_TEST_INFO = {'resource_name': _TARGET_HOST,
                     DSProps.DATASOURCE_ACTION: DatasourceAction.SNAPSHOT}


class TestScenarioEvaluator(TestFunctionalBase):

    EVALUATOR_OPTS = [
        cfg.StrOpt('templates_dir',
                   default=utils.get_resources_dir() +
                   '/templates/evaluator',
                   ),
        cfg.StrOpt('notifier_topic',
                   default='vitrage.evaluator',
                   ),
    ]

    # noinspection PyPep8Naming
    @classmethod
    def setUpClass(cls):
        cls.conf = cfg.ConfigOpts()
        cls.conf.register_opts(cls.PROCESSOR_OPTS, group='entity_graph')
        cls.conf.register_opts(cls.EVALUATOR_OPTS, group='evaluator')
        cls.conf.register_opts(cls.DATASOURCES_OPTS, group='datasources')
        TestScenarioEvaluator.load_datasources(cls.conf)
        cls.scenario_repository = ScenarioRepository(cls.conf)

    def test_deduced_state(self):

        event_queue, processor, evaluator = self._init_system()

        host_v = self._get_host_from_graph(_TARGET_HOST,
                                           processor.entity_graph)
        self.assertEqual('AVAILABLE', host_v[VProps.AGGREGATED_STATE],
                         'host should be AVAILABLE when starting')

        # generate nagios alarm to trigger template scenario
        test_vals = {'status': 'WARNING', 'service': 'cause_suboptimal_state'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        warning_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, warning_test,
                                           processor, _TARGET_HOST)
        self.assertEqual('SUBOPTIMAL', host_v[VProps.AGGREGATED_STATE],
                         'host should be SUBOPTIMAL with warning alarm')

        # next disable the alarm
        warning_test['status'] = 'OK'
        host_v = self.get_host_after_event(event_queue, warning_test,
                                           processor, _TARGET_HOST)
        self.assertEqual('AVAILABLE', host_v[VProps.AGGREGATED_STATE],
                         'host should be AVAILABLE when alarm disabled')

    def test_overlapping_deduced_state_1(self):

        event_queue, processor, evaluator = self._init_system()

        host_v = self._get_host_from_graph(_TARGET_HOST,
                                           processor.entity_graph)
        self.assertEqual('AVAILABLE', host_v[VProps.AGGREGATED_STATE],
                         'host should be AVAILABLE when starting')

        # generate nagios alarm to trigger
        test_vals = {'status': 'WARNING', 'service': 'cause_suboptimal_state'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        warning_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, warning_test,
                                           processor, _TARGET_HOST)
        self.assertEqual('SUBOPTIMAL', host_v[VProps.AGGREGATED_STATE],
                         'host should be SUBOPTIMAL with warning alarm')

        # generate CRITICAL nagios alarm to trigger
        test_vals = {'status': 'CRITICAL', 'service': 'cause_error_state'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        critical_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, critical_test,
                                           processor, _TARGET_HOST)
        self.assertEqual('ERROR', host_v[VProps.AGGREGATED_STATE],
                         'host should be ERROR with critical alarm')

        # next disable the critical alarm
        critical_test['status'] = 'OK'
        host_v = self.get_host_after_event(event_queue, critical_test,
                                           processor, _TARGET_HOST)
        self.assertEqual('SUBOPTIMAL', host_v[VProps.AGGREGATED_STATE],
                         'host should be SUBOPTIMAL with only warning alarm')

        # next disable the alarm
        warning_test['status'] = 'OK'
        host_v = self.get_host_after_event(event_queue, warning_test,
                                           processor, _TARGET_HOST)
        self.assertEqual('AVAILABLE', host_v[VProps.AGGREGATED_STATE],
                         'host should be AVAILABLE after alarm disabled')

    def test_overlapping_deduced_state_2(self):

        event_queue, processor, evaluator = self._init_system()

        host_v = self._get_host_from_graph(_TARGET_HOST,
                                           processor.entity_graph)
        self.assertEqual('AVAILABLE', host_v[VProps.AGGREGATED_STATE],
                         'host should be AVAILABLE when starting')

        # generate CRITICAL nagios alarm to trigger
        test_vals = {'status': 'CRITICAL', 'service': 'cause_error_state'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        critical_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, critical_test,
                                           processor, _TARGET_HOST)
        self.assertEqual('ERROR', host_v[VProps.AGGREGATED_STATE],
                         'host should be ERROR with critical alarm')

        # generate WARNING nagios alarm to trigger
        test_vals = {'status': 'WARNING', 'service': 'cause_suboptimal_state'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        warning_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, warning_test,
                                           processor, _TARGET_HOST)
        self.assertEqual('ERROR', host_v[VProps.AGGREGATED_STATE],
                         'host should be ERROR with critical alarm')

        # next disable the critical alarm
        critical_test['status'] = 'OK'
        host_v = self.get_host_after_event(event_queue, critical_test,
                                           processor, _TARGET_HOST)
        self.assertEqual('SUBOPTIMAL', host_v[VProps.AGGREGATED_STATE],
                         'host should be SUBOPTIMAL with only warning alarm')

    def test_deduced_alarm(self):

        event_queue, processor, evaluator = self._init_system()

        host_v = self._get_host_from_graph(_TARGET_HOST,
                                           processor.entity_graph)
        self.assertEqual('AVAILABLE', host_v[VProps.AGGREGATED_STATE],
                         'host should be AVAILABLE when starting')

        # generate CRITICAL nagios alarm to trigger
        test_vals = {'status': 'WARNING',
                     'service': 'cause_warning_deduced_alarm'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        warning_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, warning_test,
                                           processor, _TARGET_HOST)
        alarms = \
            self._get_deduced_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(1, len(alarms))
        self.assertEqual('WARNING', alarms[0]['severity'])
        causes = self._get_alarm_causes(alarms[0], processor.entity_graph)
        self.assertEqual(1, len(causes))

        # next disable the alarm
        warning_test['status'] = 'OK'
        host_v = self.get_host_after_event(event_queue, warning_test,
                                           processor, _TARGET_HOST)
        alarms = \
            self._get_deduced_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(0, len(alarms))

    # todo: (erosensw) uncomment this test
    def test_overlapping_deduced_alarm_1(self):

        event_queue, processor, evaluator = self._init_system()

        # generate WARNING nagios alarm
        vals = {'status': 'WARNING', 'service': 'cause_warning_deduced_alarm'}
        vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, vals)
        warning_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, warning_test,
                                           processor, _TARGET_HOST)
        alarms = \
            self._get_deduced_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(1, len(alarms))
        self.assertEqual('WARNING', alarms[0]['severity'])
        causes = self._get_alarm_causes(alarms[0], processor.entity_graph)
        self.assertEqual(1, len(causes))

        # generate CRITICAL nagios alarm to trigger
        vals = {'status': 'CRITICAL',
                'service': 'cause_critical_deduced_alarm'}
        vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, vals)
        critical_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, critical_test,
                                           processor, _TARGET_HOST)
        alarms = \
            self._get_deduced_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(1, len(alarms))
        self.assertEqual('CRITICAL', alarms[0]['severity'])
        causes = self._get_alarm_causes(alarms[0], processor.entity_graph)
        self.assertEqual(2, len(causes))

        # remove WARNING nagios alarm, leaving only CRITICAL one
        warning_test['status'] = 'OK'
        host_v = self.get_host_after_event(event_queue, warning_test,
                                           processor, _TARGET_HOST)
        alarms = \
            self._get_deduced_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(1, len(alarms))
        self.assertEqual('CRITICAL', alarms[0]['severity'])
        causes = self._get_alarm_causes(alarms[0], processor.entity_graph)
        self.assertEqual(1, len(causes))

        # next disable the alarm
        critical_test['status'] = 'OK'
        host_v = self.get_host_after_event(event_queue, critical_test,
                                           processor, _TARGET_HOST)
        alarms = \
            self._get_deduced_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(0, len(alarms))

    def test_overlapping_deduced_alarm_2(self):

        event_queue, processor, evaluator = self._init_system()

        # generate CRITICAL nagios alarm to trigger
        test_vals = {'status': 'CRITICAL',
                     'service': 'cause_critical_deduced_alarm'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        critical_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, critical_test,
                                           processor, _TARGET_HOST)
        alarms = \
            self._get_deduced_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(1, len(alarms))
        self.assertEqual('CRITICAL', alarms[0]['severity'])

        # generate WARNING nagios alarm to trigger
        test_vals = {'status': 'WARNING',
                     'service': 'cause_warning_deduced_alarm'}
        test_vals.update(_NAGIOS_TEST_INFO)
        generator = mock_driver.simple_nagios_alarm_generators(1, 1, test_vals)
        warning_test = mock_driver.generate_random_events_list(generator)[0]

        host_v = self.get_host_after_event(event_queue, warning_test,
                                           processor, _TARGET_HOST)
        alarms = \
            self._get_deduced_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(1, len(alarms))
        self.assertEqual('CRITICAL', alarms[0]['severity'])

        # remove CRITICAL nagios alarm, leaving only WARNING one
        critical_test['status'] = 'OK'
        host_v = self.get_host_after_event(event_queue, critical_test,
                                           processor, _TARGET_HOST)
        alarms = \
            self._get_deduced_alarms_on_host(host_v, processor.entity_graph)
        self.assertEqual(1, len(alarms))
        self.assertEqual('WARNING', alarms[0]['severity'])

    def get_host_after_event(self, event_queue, nagios_event,
                             processor, target_host):
        processor.process_event(nagios_event)
        while not event_queue.empty():
            processor.process_event(event_queue.get())
        host_v = self._get_host_from_graph(target_host,
                                           processor.entity_graph)
        return host_v

    def _init_system(self):
        processor = self._create_processor_with_graph(self.conf)
        event_queue = queue.Queue()
        evaluator = ScenarioEvaluator(self.conf, processor.entity_graph,
                                      self.scenario_repository, event_queue,
                                      enabled=True)
        return event_queue, processor, evaluator

    @staticmethod
    def _get_host_from_graph(host_name, entity_graph):
        vertex_attrs = {VProps.TYPE: NOVA_HOST_DATASOURCE,
                        VProps.NAME: host_name}
        host_vertices = entity_graph.get_vertices(
            vertex_attr_filter=vertex_attrs)
        assert len(host_vertices) == 1, "incorrect number of vertices"
        return host_vertices[0]

    @staticmethod
    def _get_deduced_alarms_on_host(host_v, entity_graph):
        v_id = host_v.vertex_id
        vertex_attrs = {VProps.NAME: 'deduced_alarm',
                        VProps.IS_DELETED: False, }
        return entity_graph.neighbors(v_id=v_id,
                                      vertex_attr_filter=vertex_attrs)

    @staticmethod
    def _get_alarm_causes(alarm_v, entity_graph):
        v_id = alarm_v.vertex_id
        edge_attrs = {EProps.RELATIONSHIP_TYPE: "causes",
                      EProps.IS_DELETED: False, }
        return entity_graph.neighbors(v_id=v_id, edge_attr_filter=edge_attrs)
