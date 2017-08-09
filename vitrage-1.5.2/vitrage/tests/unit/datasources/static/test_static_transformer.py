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

import datetime

from oslo_config import cfg
from oslo_log import log as logging

from vitrage.common.constants import DatasourceProperties as DSProps
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import TopologyFields
from vitrage.common.constants import UpdateMethod
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources.nova.host import NOVA_HOST_DATASOURCE
from vitrage.datasources.nova.host.transformer import HostTransformer
from vitrage.datasources.static import STATIC_DATASOURCE
from vitrage.datasources.static.transformer import StaticTransformer
from vitrage.tests import base
from vitrage.tests.mocks import mock_driver

LOG = logging.getLogger(__name__)


class TestStaticTransformer(base.BaseTest):

    OPTS = [
        cfg.StrOpt('update_method',
                   default=UpdateMethod.PULL),
    ]

    # noinspection PyAttributeOutsideInit,PyPep8Naming
    @classmethod
    def setUpClass(cls):
        cls.transformers = {}
        cls.conf = cfg.ConfigOpts()
        cls.conf.register_opts(cls.OPTS, group=STATIC_DATASOURCE)
        cls.transformer = StaticTransformer(cls.transformers, cls.conf)
        cls.transformers[STATIC_DATASOURCE] = cls.transformer
        cls.transformers[NOVA_HOST_DATASOURCE] = \
            HostTransformer(cls.transformers, cls.conf)

    # noinspection PyAttributeOutsideInit
    def setUp(self):
        super(TestStaticTransformer, self).setUp()
        self.entity_type = STATIC_DATASOURCE
        self.entity_id = '12345'
        self.timestamp = datetime.datetime.utcnow()

    def test_create_placeholder_vertex(self):
        properties = {
            VProps.TYPE: self.entity_type,
            VProps.ID: self.entity_id,
            VProps.CATEGORY: EntityCategory.RESOURCE,
            VProps.SAMPLE_TIMESTAMP: self.timestamp
        }
        placeholder = self.transformer.create_neighbor_placeholder_vertex(
            **properties)

        observed_entity_id = placeholder.vertex_id
        expected_entity_id = 'RESOURCE:static:12345'
        self.assertEqual(observed_entity_id, expected_entity_id)

        observed_time = placeholder.get(VProps.SAMPLE_TIMESTAMP)
        self.assertEqual(observed_time, self.timestamp)

        observed_subtype = placeholder.get(VProps.TYPE)
        self.assertEqual(observed_subtype, self.entity_type)

        observed_entity_id = placeholder.get(VProps.ID)
        self.assertEqual(observed_entity_id, self.entity_id)

        observed_category = placeholder.get(VProps.CATEGORY)
        self.assertEqual(observed_category, EntityCategory.RESOURCE)

        is_placeholder = placeholder.get(VProps.IS_PLACEHOLDER)
        self.assertEqual(is_placeholder, True)

    def test_snapshot_transform(self):
        vals_list = mock_driver.simple_static_generators(snapshot_events=1)
        events = mock_driver.generate_random_events_list(vals_list)
        self._event_transform_test(events)

    def test_update_transform(self):
        vals_list = mock_driver.simple_static_generators(update_events=1)
        events = mock_driver.generate_random_events_list(vals_list)
        self._event_transform_test(events)

    def _event_transform_test(self, events):
        for event in events:
            wrapper = self.transformer.transform(event)

            vertex = wrapper.vertex
            self._validate_vertex(vertex, event)

            neighbors = wrapper.neighbors
            self._validate_neighbors(neighbors, vertex.vertex_id, event)

    def _validate_vertex(self, vertex, event):
        self._validate_common_props(vertex, event)
        self.assertEqual(vertex[VProps.SAMPLE_TIMESTAMP],
                         event[DSProps.SAMPLE_DATE])

        for k, v in event.get(TopologyFields.METADATA, {}):
            self.assertEqual(vertex[k], v)

    def _validate_common_props(self, vertex, event):
        self.assertEqual(vertex[VProps.CATEGORY], EntityCategory.RESOURCE)
        self.assertEqual(vertex[VProps.TYPE], event[VProps.TYPE])
        self.assertEqual(vertex[VProps.ID], event[VProps.ID])
        self.assertFalse(vertex[VProps.IS_DELETED])

    def _validate_neighbors(self, neighbors, vertex_id, event):
        for i in range(len(neighbors)):
            self._validate_neighbor(neighbors[i],
                                    event[TopologyFields.RELATIONSHIPS][i],
                                    vertex_id)

    def _validate_neighbor(self, neighbor, rel, vertex_id):
        vertex = neighbor.vertex
        self._validate_neighbor_vertex_props(vertex,
                                             rel[TopologyFields.TARGET])

        edge = neighbor.edge
        self.assertEqual(edge.source_id, vertex_id)
        self.assertEqual(edge.target_id, neighbor.vertex.vertex_id)
        self.assertEqual(edge.label, rel[TopologyFields.RELATIONSHIP_TYPE])

    def _validate_neighbor_vertex_props(self, vertex, event):
        self._validate_common_props(vertex, event)
        self.assertTrue(vertex[VProps.IS_PLACEHOLDER])
