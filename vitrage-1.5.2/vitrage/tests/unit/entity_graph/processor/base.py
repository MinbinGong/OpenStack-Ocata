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

from oslo_config import cfg

from vitrage.common.constants import VertexProperties
from vitrage.entity_graph import transformer_manager
from vitrage.graph import driver as graph
from vitrage.tests.unit.entity_graph.base import TestEntityGraphUnitBase


class TestBaseProcessor(TestEntityGraphUnitBase):

    # noinspection PyAttributeOutsideInit,PyPep8Naming
    @classmethod
    def setUpClass(cls):
        super(TestBaseProcessor, cls).setUpClass()
        cls.conf = cfg.ConfigOpts()
        cls.conf.register_opts(cls.DATASOURCES_OPTS, group='datasources')
        cls.load_datasources(cls.conf)
        cls.transform = transformer_manager.TransformerManager(cls.conf)

    @staticmethod
    def _update_vertex_to_graph(entity_graph, category, type_, id_,
                                is_deleted, is_placeholder_data,
                                additional_prop):
        # create vertex properties
        prop = {key: value for key, value in additional_prop.items()}
        prop[VertexProperties.CATEGORY] = category
        prop[VertexProperties.TYPE] = type_
        prop[VertexProperties.ID] = id_
        prop[VertexProperties.IS_DELETED] = is_deleted
        prop[VertexProperties.IS_PLACEHOLDER] = is_placeholder_data

        # TODO(Alexey): change back to original method
        # vertex_id = self.transform.get_key(prop)
        vertex_id = category + "_" + type_ + "_" + id_
        vertex = graph.Vertex(vertex_id, prop)
        entity_graph.add_vertex(vertex)

        return vertex

    @staticmethod
    def _update_edge_to_graph(entity_graph, src_id, trgt_id, label):
        edge = graph.Edge(src_id, trgt_id, label, {})
        entity_graph.add_edge(edge)
        return edge
