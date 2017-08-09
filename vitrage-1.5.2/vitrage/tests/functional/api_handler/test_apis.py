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

import json

from vitrage.api_handler.apis.alarm import AlarmApis
from vitrage.api_handler.apis.rca import RcaApis
from vitrage.api_handler.apis.topology import TopologyApis
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources import NOVA_HOST_DATASOURCE
from vitrage.datasources import NOVA_INSTANCE_DATASOURCE
from vitrage.datasources import NOVA_ZONE_DATASOURCE
from vitrage.datasources import OPENSTACK_CLUSTER
from vitrage.graph.driver.networkx_graph import NXGraph
import vitrage.graph.utils as graph_utils
from vitrage.tests.unit.entity_graph.base import TestEntityGraphUnitBase


class TestApis(TestEntityGraphUnitBase):

    def test_get_alarms_with_admin_project(self):
        # Setup
        graph = self._create_graph()
        apis = AlarmApis(graph, None)
        ctx = {'tenant': 'project_1', 'is_admin': True}

        # Action
        alarms = apis.get_alarms(ctx, vitrage_id='all', all_tenants='0')
        alarms = json.loads(alarms)['alarms']

        # Test assertions
        self.assertEqual(3, len(alarms))
        self._check_projects_entities(alarms, 'project_1', True)

    def test_get_alarms_with_not_admin_project(self):
        # Setup
        graph = self._create_graph()
        apis = AlarmApis(graph, None)
        ctx = {'tenant': 'project_2', 'is_admin': False}

        # Action
        alarms = apis.get_alarms(ctx, vitrage_id='all', all_tenants='0')
        alarms = json.loads(alarms)['alarms']

        # Test assertions
        self.assertEqual(2, len(alarms))
        self._check_projects_entities(alarms, 'project_2', True)

    def test_get_alarms_with_all_tenants(self):
        # Setup
        graph = self._create_graph()
        apis = AlarmApis(graph, None)
        ctx = {'tenant': 'project_1', 'is_admin': False}

        # Action
        alarms = apis.get_alarms(ctx, vitrage_id='all', all_tenants='1')
        alarms = json.loads(alarms)['alarms']

        # Test assertions
        self.assertEqual(5, len(alarms))
        self._check_projects_entities(alarms, None, True)

    def test_get_rca_with_admin_project(self):
        # Setup
        graph = self._create_graph()
        apis = RcaApis(graph, None)
        ctx = {'tenant': 'project_1', 'is_admin': True}

        # Action
        graph_rca = apis.get_rca(ctx, root='alarm_on_host', all_tenants='0')
        graph_rca = json.loads(graph_rca)

        # Test assertions
        self.assertEqual(3, len(graph_rca['nodes']))
        self._check_projects_entities(graph_rca['nodes'], 'project_1', True)

    def test_get_rca_with_not_admin_project(self):
        # Setup
        graph = self._create_graph()
        apis = RcaApis(graph, None)
        ctx = {'tenant': 'project_2', 'is_admin': False}

        # Action
        graph_rca = apis.get_rca(ctx,
                                 root='alarm_on_instance_3',
                                 all_tenants='0')
        graph_rca = json.loads(graph_rca)

        # Test assertions
        self.assertEqual(2, len(graph_rca['nodes']))
        self._check_projects_entities(graph_rca['nodes'], 'project_2', True)

    def test_get_rca_with_not_admin_bla_project(self):
        # Setup
        graph = self._create_graph()
        apis = RcaApis(graph, None)
        ctx = {'tenant': 'project_2', 'is_admin': False}

        # Action
        graph_rca = apis.get_rca(ctx, root='alarm_on_host', all_tenants='0')
        graph_rca = json.loads(graph_rca)

        # Test assertions
        self.assertEqual(3, len(graph_rca['nodes']))
        self._check_projects_entities(graph_rca['nodes'], 'project_2', True)

    def test_get_rca_with_all_tenants(self):
        # Setup
        graph = self._create_graph()
        apis = RcaApis(graph, None)
        ctx = {'tenant': 'project_1', 'is_admin': False}

        # Action
        graph_rca = apis.get_rca(ctx, root='alarm_on_host', all_tenants='1')
        graph_rca = json.loads(graph_rca)

        # Test assertions
        self.assertEqual(5, len(graph_rca['nodes']))
        self._check_projects_entities(graph_rca['nodes'], None, True)

    def test_get_topology_with_admin_project(self):
        # Setup
        graph = self._create_graph()
        apis = TopologyApis(graph, None)
        ctx = {'tenant': 'project_1', 'is_admin': True}

        # Action
        graph_topology = apis.get_topology(
            ctx,
            graph_type='graph',
            depth=10,
            query=None,
            root='RESOURCE:openstack.cluster:OpenStack Cluster',
            all_tenants=0)
        graph_topology = json.loads(graph_topology)

        # Test assertions
        self.assertEqual(8, len(graph_topology['nodes']))
        self._check_projects_entities(graph_topology['nodes'],
                                      'project_1',
                                      False)

    def test_get_topology_with_not_admin_project(self):
        # Setup
        graph = self._create_graph()
        apis = TopologyApis(graph, None)
        ctx = {'tenant': 'project_2', 'is_admin': False}

        # Action
        graph_topology = apis.get_topology(
            ctx,
            graph_type='graph',
            depth=10,
            query=None,
            root='RESOURCE:openstack.cluster:OpenStack Cluster',
            all_tenants=0)
        graph_topology = json.loads(graph_topology)

        # Test assertions
        self.assertEqual(7, len(graph_topology['nodes']))
        self._check_projects_entities(graph_topology['nodes'],
                                      'project_2',
                                      False)

    def test_get_topology_with_all_tenants(self):
        # Setup
        graph = self._create_graph()
        apis = TopologyApis(graph, None)
        ctx = {'tenant': 'project_1', 'is_admin': False}

        # Action
        graph_topology = apis.get_topology(
            ctx,
            graph_type='graph',
            depth=10,
            query=None,
            root='RESOURCE:openstack.cluster:OpenStack Cluster',
            all_tenants=1)
        graph_topology = json.loads(graph_topology)

        # Test assertions
        self.assertEqual(12, len(graph_topology['nodes']))

    def _check_projects_entities(self,
                                 alarms,
                                 project_id,
                                 check_alarm_category):
        for alarm in alarms:
            tmp_project_id = alarm.get(VProps.PROJECT_ID, None)
            condition = True
            if check_alarm_category:
                condition = alarm[VProps.CATEGORY] == EntityCategory.ALARM
            if project_id:
                condition = condition and \
                    (not tmp_project_id or
                     (tmp_project_id and tmp_project_id == project_id))
            self.assertEqual(True, condition)

    def _create_graph(self):
        graph = NXGraph('Multi tenancy graph')

        # create vertices
        cluster_vertex = self._create_resource(
            'RESOURCE:openstack.cluster:OpenStack Cluster',
            OPENSTACK_CLUSTER)
        zone_vertex = self._create_resource('zone_1',
                                            NOVA_ZONE_DATASOURCE)
        host_vertex = self._create_resource('host_1',
                                            NOVA_HOST_DATASOURCE)
        instance_1_vertex = self._create_resource('instance_1',
                                                  NOVA_INSTANCE_DATASOURCE,
                                                  project_id='project_1')
        instance_2_vertex = self._create_resource('instance_2',
                                                  NOVA_INSTANCE_DATASOURCE,
                                                  project_id='project_1')
        instance_3_vertex = self._create_resource('instance_3',
                                                  NOVA_INSTANCE_DATASOURCE,
                                                  project_id='project_2')
        instance_4_vertex = self._create_resource('instance_4',
                                                  NOVA_INSTANCE_DATASOURCE,
                                                  project_id='project_2')
        alarm_on_host_vertex = self._create_alarm('alarm_on_host',
                                                  'alarm_on_host')
        alarm_on_instance_1_vertex = self._create_alarm('alarm_on_instance_1',
                                                        'deduced_alarm',
                                                        project_id='project_1')
        alarm_on_instance_2_vertex = self._create_alarm('alarm_on_instance_2',
                                                        'deduced_alarm')
        alarm_on_instance_3_vertex = self._create_alarm('alarm_on_instance_3',
                                                        'deduced_alarm',
                                                        project_id='project_2')
        alarm_on_instance_4_vertex = self._create_alarm('alarm_on_instance_4',
                                                        'deduced_alarm')

        # create links
        edges = list()
        edges.append(graph_utils.create_edge(
            cluster_vertex.vertex_id,
            zone_vertex.vertex_id,
            'contains'))
        edges.append(graph_utils.create_edge(
            zone_vertex.vertex_id,
            host_vertex.vertex_id,
            'contains'))
        edges.append(graph_utils.create_edge(
            host_vertex.vertex_id,
            instance_1_vertex.vertex_id,
            'contains'))
        edges.append(graph_utils.create_edge(
            host_vertex.vertex_id,
            instance_2_vertex.vertex_id,
            'contains'))
        edges.append(graph_utils.create_edge(
            host_vertex.vertex_id,
            instance_3_vertex.vertex_id,
            'contains'))
        edges.append(graph_utils.create_edge(
            host_vertex.vertex_id,
            instance_4_vertex.vertex_id,
            'contains'))
        edges.append(graph_utils.create_edge(
            alarm_on_host_vertex.vertex_id,
            host_vertex.vertex_id,
            'on'))
        edges.append(graph_utils.create_edge(
            alarm_on_instance_1_vertex.vertex_id,
            instance_1_vertex.vertex_id,
            'on'))
        edges.append(graph_utils.create_edge(
            alarm_on_instance_2_vertex.vertex_id,
            instance_2_vertex.vertex_id,
            'on'))
        edges.append(graph_utils.create_edge(
            alarm_on_instance_3_vertex.vertex_id,
            instance_3_vertex.vertex_id,
            'on'))
        edges.append(graph_utils.create_edge(
            alarm_on_instance_4_vertex.vertex_id,
            instance_4_vertex.vertex_id,
            'on'))
        edges.append(graph_utils.create_edge(
            alarm_on_host_vertex.vertex_id,
            alarm_on_instance_1_vertex.vertex_id,
            'causes'))
        edges.append(graph_utils.create_edge(
            alarm_on_host_vertex.vertex_id,
            alarm_on_instance_2_vertex.vertex_id,
            'causes'))
        edges.append(graph_utils.create_edge(
            alarm_on_host_vertex.vertex_id,
            alarm_on_instance_3_vertex.vertex_id,
            'causes'))
        edges.append(graph_utils.create_edge(
            alarm_on_host_vertex.vertex_id,
            alarm_on_instance_4_vertex.vertex_id,
            'causes'))

        # add vertices to graph
        graph.add_vertex(cluster_vertex)
        graph.add_vertex(zone_vertex)
        graph.add_vertex(host_vertex)
        graph.add_vertex(instance_1_vertex)
        graph.add_vertex(instance_2_vertex)
        graph.add_vertex(instance_3_vertex)
        graph.add_vertex(instance_4_vertex)
        graph.add_vertex(alarm_on_host_vertex)
        graph.add_vertex(alarm_on_instance_1_vertex)
        graph.add_vertex(alarm_on_instance_2_vertex)
        graph.add_vertex(alarm_on_instance_3_vertex)
        graph.add_vertex(alarm_on_instance_4_vertex)

        # add links to graph
        for edge in edges:
            graph.add_edge(edge)

        return graph
