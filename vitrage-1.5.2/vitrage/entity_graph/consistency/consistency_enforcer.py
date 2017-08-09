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

from datetime import timedelta
import time

from oslo_log import log

from vitrage.common.constants import DatasourceAction
from vitrage.common.constants import DatasourceProperties as DSProps
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import GraphAction
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources.consistency import CONSISTENCY_DATASOURCE
from vitrage.datasources import OPENSTACK_CLUSTER
from vitrage.evaluator.actions.evaluator_event_transformer import VITRAGE_TYPE
from vitrage.utils.datetime import utcnow

LOG = log.getLogger(__name__)


class ConsistencyEnforcer(object):

    def __init__(self,
                 conf,
                 evaluator_queue,
                 evaluator,
                 entity_graph,
                 initialization_status):
        self.conf = conf
        self.evaluator_queue = evaluator_queue
        self.evaluator = evaluator
        self.graph = entity_graph
        self.initialization_status = initialization_status

    def initializing_process(self):
        try:
            LOG.info('Consistency Initializing Process - Started')

            if not self._wait_for_action(
                    self.initialization_status.is_received_all_end_messages):
                LOG.error('Maximum retries for consistency initializator '
                          'were done')

            LOG.info('All end messages were received')

            self.evaluator.enabled = True
            timestamp = str(utcnow())
            all_vertices = self.graph.get_vertices()

            self._run_evaluator(all_vertices)

            self._wait_for_processing_evaluator_events()

            self._mark_old_deduced_alarms_as_deleted(timestamp)

            self.initialization_status.status = \
                self.initialization_status.FINISHED

            LOG.info('Consistency Initializing Process - Finished')
        except Exception as e:
            LOG.exception('Error in deleting vertices from entity_graph: %s',
                          e)

    def periodic_process(self):
        try:
            LOG.debug('Consistency Periodic Process - Started')

            # remove is_deleted=True entities
            old_deleted_entities = self._find_old_deleted_entities()
            LOG.debug('Found %s vertices to be deleted by consistency service'
                      ': %s', len(old_deleted_entities), old_deleted_entities)
            self._push_events_to_queue(old_deleted_entities,
                                       GraphAction.REMOVE_DELETED_ENTITY)

            # mark stale entities as is_deleted=True
            stale_entities = self._find_stale_entities()
            LOG.debug('Found %s vertices to be marked as deleted by '
                      'consistency service: %s', len(stale_entities),
                      stale_entities)
            self._push_events_to_queue(stale_entities,
                                       GraphAction.DELETE_ENTITY)
        except Exception as e:
            LOG.exception(
                'Error in deleting vertices from entity_graph: %s', e)

    def _find_stale_entities(self):
        query = {
            'and': [
                {'!=': {VProps.TYPE: VITRAGE_TYPE}},
                {'<': {VProps.SAMPLE_TIMESTAMP: str(utcnow() - timedelta(
                    seconds=2 * self.conf.datasources.snapshots_interval))}},
                {'==': {VProps.IS_DELETED: False}}
            ]
        }

        vertices = self.graph.get_vertices(query_dict=query)

        return set(self._filter_vertices_to_be_deleted(vertices))

    def _find_old_deleted_entities(self):
        query = {
            'and': [
                {'==': {VProps.IS_DELETED: True}},
                {'<': {VProps.SAMPLE_TIMESTAMP: str(utcnow() - timedelta(
                    seconds=self.conf.consistency.min_time_to_delete))}}
            ]
        }

        vertices = self.graph.get_vertices(query_dict=query)

        return self._filter_vertices_to_be_deleted(vertices)

    def _find_old_deduced_alarms(self, timestamp):
        query = {
            'and': [
                {'==': {VProps.CATEGORY: EntityCategory.ALARM}},
                {'==': {VProps.TYPE: VITRAGE_TYPE}},
                {'<': {VProps.SAMPLE_TIMESTAMP: timestamp}}
            ]
        }
        return self.graph.get_vertices(query_dict=query)

    def _run_evaluator(self, vertices):
        start_time = time.time()
        for vertex in vertices:
            self.evaluator.process_event(None, vertex, True)
        LOG.info('Run Evaluator on %s items - took %s', str(len(vertices)),
                 str(time.time() - start_time))

    def _wait_for_processing_evaluator_events(self):
        # wait for multiprocessing to put the events in the queue
        time.sleep(1)

        self._wait_for_action(self.evaluator_queue.empty)

    def _mark_old_deduced_alarms_as_deleted(self, timestamp):
        old_deduced_alarms = self._find_old_deduced_alarms(timestamp)
        self._push_events_to_queue(old_deduced_alarms,
                                   GraphAction.DELETE_ENTITY)

    def _push_events_to_queue(self, vertices, action):
        for vertex in vertices:
            event = {
                DSProps.ENTITY_TYPE: CONSISTENCY_DATASOURCE,
                DSProps.DATASOURCE_ACTION: DatasourceAction.UPDATE,
                DSProps.SAMPLE_DATE: str(utcnow()),
                DSProps.EVENT_TYPE: action,
                VProps.VITRAGE_ID: vertex[VProps.VITRAGE_ID]
            }
            self.evaluator_queue.put(event)

    @staticmethod
    def _filter_vertices_to_be_deleted(vertices):
        return list(filter(
            lambda ver:
            not (ver[VProps.CATEGORY] == EntityCategory.RESOURCE and
                 ver[VProps.TYPE] == OPENSTACK_CLUSTER), vertices))

    def _wait_for_action(self, function):
        count_retries = 0
        while True:
            if count_retries >= \
                    self.conf.consistency.initialization_max_retries:
                return False

            if function():
                return True

            count_retries += 1
            time.sleep(self.conf.consistency.initialization_interval)
