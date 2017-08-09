# Copyright 2016 - Alcatel-Lucent
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

"""
test_vitrage graph algorithms
----------------------------------

Tests for `vitrage` graph driver algorithms
"""


from vitrage.common.constants import EdgeLabel
from vitrage.common.constants import EdgeProperties as EProps
from vitrage.common.constants import VertexProperties as VProps
from vitrage.graph.algo_driver.algorithm import Mapping
from vitrage.graph.driver.elements import Edge
from vitrage.graph.driver.graph import Direction
from vitrage.tests.unit.graph.base import *  # noqa


class GraphAlgorithmTest(GraphTestBase):

    # noinspection PyPep8Naming
    @classmethod
    def setUpClass(cls):
        cls.vm_id = 10000000
        cls.vm_alarm_id = 30000000
        cls.vms = []
        cls.host_alarm_id = 20000000
        cls.host_test_id = 40000000
        cls.entity_graph = cls._create_entity_graph(
            'entity_graph',
            num_of_hosts_per_node=ENTITY_GRAPH_HOSTS_PER_CLUSTER,
            num_of_vms_per_host=ENTITY_GRAPH_VMS_PER_HOST,
            num_of_alarms_per_host=ENTITY_GRAPH_ALARMS_PER_HOST,
            num_of_alarms_per_vm=ENTITY_GRAPH_ALARMS_PER_VM,
            num_of_tests_per_host=ENTITY_GRAPH_TESTS_PER_HOST)

    def test_graph_query_vertices(self):
        ga = self.entity_graph.algo

        query = {'==': {VProps.TYPE: OPENSTACK_CLUSTER}}
        subgraph = ga.graph_query_vertices(query)
        self.assertEqual(
            1,  # For Cluster
            subgraph.num_vertices(), 'num of vertex node')

        query = {
            'or': [
                {'==': {VProps.TYPE: NOVA_HOST_DATASOURCE}},
                {'==': {VProps.TYPE: OPENSTACK_CLUSTER}}
            ]
        }

        subgraph = ga.graph_query_vertices(query)
        self.assertEqual(
            ENTITY_GRAPH_HOSTS_PER_CLUSTER,
            subgraph.num_edges(), 'num of edges Host <-- NODE')

        query = {
            'or': [
                {'==': {VProps.TYPE: NOVA_INSTANCE_DATASOURCE}},
                {'==': {VProps.CATEGORY: ALARM}},
                {'==': {VProps.TYPE: NOVA_HOST_DATASOURCE}},
                {'==': {VProps.TYPE: OPENSTACK_CLUSTER}}
            ]
        }
        subgraph = ga.graph_query_vertices(query)
        self.assertEqual(
            ENTITY_GRAPH_HOSTS_PER_CLUSTER +
            ENTITY_GRAPH_HOSTS_PER_CLUSTER * ENTITY_GRAPH_ALARMS_PER_HOST +
            ENTITY_GRAPH_HOSTS_PER_CLUSTER * ENTITY_GRAPH_VMS_PER_HOST +
            ENTITY_GRAPH_HOSTS_PER_CLUSTER * ENTITY_GRAPH_VMS_PER_HOST *
            ENTITY_GRAPH_ALARMS_PER_VM,
            subgraph.num_edges(), 'num of BOTH edges Host (depth 1)')

        # Get first host ID
        neighboring_hosts = self.entity_graph.neighbors(
            v_node.vertex_id, {VProps.TYPE: NOVA_HOST_DATASOURCE})
        first_host_id = neighboring_hosts.pop().vertex_id

        query = {'!=': {'NOTHING': 'IS EVERYTHING'}}
        subgraph = ga.graph_query_vertices(
            query_dict=query, root_id=first_host_id, depth=1)
        self.assertEqual(
            1 +  # For host
            1 +  # For Cluster
            ENTITY_GRAPH_ALARMS_PER_HOST +
            ENTITY_GRAPH_TESTS_PER_HOST +
            ENTITY_GRAPH_VMS_PER_HOST,
            subgraph.num_edges(), 'num of BOTH edges Host (depth 1)')

        query = {
            'or': [
                {'==': {VProps.TYPE: SWITCH}},
                {'==': {VProps.TYPE: NOVA_HOST_DATASOURCE}},
            ]
        }
        subgraph = ga.graph_query_vertices(
            query_dict=query, root_id=first_host_id, depth=1)
        self.assertEqual(
            1,  # For SWITCH
            subgraph.num_edges(), 'num of BOTH edges Host (depth 1)')

        subgraph = ga.graph_query_vertices(root_id=first_host_id, depth=2)
        self.assertEqual(
            1 +  # Cluster to switch
            ENTITY_GRAPH_HOSTS_PER_CLUSTER * 2 +
            ENTITY_GRAPH_ALARMS_PER_HOST +
            ENTITY_GRAPH_TESTS_PER_HOST +
            ENTITY_GRAPH_VMS_PER_HOST +
            ENTITY_GRAPH_VMS_PER_HOST * ENTITY_GRAPH_ALARMS_PER_VM,
            subgraph.num_edges(), 'num of BOTH edges Host (depth 2)')

        subgraph = ga.graph_query_vertices(root_id=first_host_id, depth=3,
                                           direction=Direction.OUT)
        self.assertEqual(
            1 +
            ENTITY_GRAPH_VMS_PER_HOST,
            subgraph.num_edges(), 'num of BOTH edges Host (depth 3)')

        query = {
            'and': [
                {'!=': {VProps.TYPE: ALARM_ON_VM}},
                {'!=': {VProps.TYPE: ALARM_ON_HOST}},
                {'!=': {VProps.CATEGORY: ALARM}}
            ]
        }
        subgraph = ga.graph_query_vertices(query_dict=query, depth=3)
        self.assertEqual(
            1 +  # Cluster to switch
            ENTITY_GRAPH_HOSTS_PER_CLUSTER * 2 +
            ENTITY_GRAPH_HOSTS_PER_CLUSTER * ENTITY_GRAPH_TESTS_PER_HOST +
            ENTITY_GRAPH_HOSTS_PER_CLUSTER * ENTITY_GRAPH_VMS_PER_HOST,
            subgraph.num_edges(), 'num of edges Node (depth 3)')

        query = {
            'or': [
                {'==': {VProps.TYPE: OPENSTACK_CLUSTER}},
                {'==': {VProps.CATEGORY: ALARM}},
            ]
        }
        subgraph = ga.graph_query_vertices(query_dict=query, depth=3)
        self.assertEqual(0, subgraph.num_edges(),
                         'num of BOTH edges Node (depth 3)')
        self.assertEqual(1, subgraph.num_vertices(),
                         'num of BOTH vertices Node (depth 3)')

        # check the edge_query_dict parameter
        query = {'!=': {'NOTHING': 'IS EVERYTHING'}}
        edge_query = {'==': {EProps.RELATIONSHIP_TYPE: EdgeLabel.CONTAINS}}
        subgraph = ga.graph_query_vertices(
            query_dict=query, depth=5, edge_query_dict=edge_query)
        alarms = subgraph.get_vertices(
            vertex_attr_filter={VProps.CATEGORY: ALARM})
        self.assertEqual(len(alarms), 0, 'We filtered the ON relationship,'
                                         ' so no alarms should exist')

        # check that the is_deleted=True edges are deleted from the graph
        hosts_query = {VProps.CATEGORY: 'RESOURCE',
                       VProps.TYPE: NOVA_HOST_DATASOURCE}
        hosts = self.entity_graph.get_vertices(
            vertex_attr_filter=hosts_query)
        instances_query = {VProps.CATEGORY: 'RESOURCE',
                           VProps.TYPE: NOVA_INSTANCE_DATASOURCE}
        instances = self.entity_graph.get_vertices(
            vertex_attr_filter=instances_query)
        instance_edges = self.entity_graph.get_edges(instances[0].vertex_id)

        for edge in instance_edges:
            if 'nova.host' in edge.source_id:
                host_instance_edge = edge
        host_instance_edge[VProps.IS_DELETED] = True
        self.entity_graph.update_edge(host_instance_edge)

        edges_query = {'relationship_type': 'contains', 'is_deleted': False}
        if host_instance_edge.source_id != hosts[0].vertex_id:
            new_edge = Edge(hosts[0].vertex_id, instances[0].vertex_id,
                            EdgeLabel.CONTAINS, properties=edges_query)
            self.entity_graph.update_edge(new_edge)
        else:
            new_edge = Edge(hosts[1].vertex_id, instances[0].vertex_id,
                            EdgeLabel.CONTAINS, properties=edges_query)
            self.entity_graph.update_edge(new_edge)

        query = {'!=': {'NOTHING': 'IS EVERYTHING'}}
        edge_query = {'==': {EProps.IS_DELETED: False}}
        subgraph = ga.graph_query_vertices(
            query_dict=query, depth=5, edge_query_dict=edge_query)
        self.assertEqual(self.entity_graph.num_edges() - 1,
                         subgraph.num_edges(),
                         'We filtered the ON relationship, so no alarms '
                         'should exist')

        # Undo changes made by this test
        host_instance_edge[VProps.IS_DELETED] = False
        self.entity_graph.update_edge(host_instance_edge)
        self.entity_graph.remove_edge(new_edge)

    def test_no_match_graph_query_vertices(self):
        query = {'==': {VProps.TYPE: 'test'}}
        subgraph = self.entity_graph.algo.graph_query_vertices(query)
        self.assertEqual(
            0,
            subgraph.num_vertices(), 'num of vertex node')

    def test_template_matching(self):
        """Test the template matching algorithm

        Using the entity graph (created above) as a big graph we search
        for a sub graph match
        """
        ga = self.entity_graph.algo

        # Get ids of some of the elements in the entity graph:
        vm_alarm = self.entity_graph.get_vertex(
            ALARM_ON_VM + str(self.vm_alarm_id - 1))
        host_alarm = self.entity_graph.get_vertex(
            ALARM_ON_HOST + str(self.host_alarm_id - 1))

        # Create a template for template matching
        t = NXGraph('template_graph')
        t_v_host_alarm = graph_utils.create_vertex(
            vitrage_id='1', entity_category=ALARM, entity_type=ALARM_ON_HOST)
        t_v_alarm_fail = graph_utils.create_vertex(
            vitrage_id='1', entity_category=ALARM, entity_type='fail')
        t_v_host = graph_utils.create_vertex(
            vitrage_id='2',
            entity_category=RESOURCE,
            entity_type=NOVA_HOST_DATASOURCE)
        t_v_vm = graph_utils.create_vertex(
            vitrage_id='3',
            entity_category=RESOURCE,
            entity_type=NOVA_INSTANCE_DATASOURCE)
        t_v_vm_alarm = graph_utils.create_vertex(
            vitrage_id='4', entity_category=ALARM, entity_type=ALARM_ON_VM)
        t_v_switch = graph_utils.create_vertex(
            vitrage_id='5', entity_category=RESOURCE, entity_type=SWITCH)
        t_v_node = graph_utils.create_vertex(
            vitrage_id='6',
            entity_category=RESOURCE,
            entity_type=OPENSTACK_CLUSTER)
        t_v_node_not_in_graph = graph_utils.create_vertex(
            vitrage_id='7', entity_category=RESOURCE,
            entity_type=OPENSTACK_CLUSTER + ' not in graph')

        e_alarm_on_host = graph_utils.create_edge(
            t_v_host_alarm.vertex_id, t_v_host.vertex_id, ELabel.ON)
        e_host_contains_vm = graph_utils.create_edge(
            t_v_host.vertex_id, t_v_vm.vertex_id, ELabel.CONTAINS)
        e_alarm_on_vm = graph_utils.create_edge(
            t_v_vm_alarm.vertex_id, t_v_vm.vertex_id, ELabel.ON)
        e_host_uses_switch = graph_utils.create_edge(
            t_v_host.vertex_id, t_v_switch.vertex_id, 'USES')
        e_node_contains_host = graph_utils.create_edge(
            t_v_node.vertex_id, t_v_host.vertex_id, ELabel.CONTAINS)
        e_node_contains_switch = graph_utils.create_edge(
            t_v_node.vertex_id, t_v_switch.vertex_id, ELabel.CONTAINS)
        e_node_contains_switch_fail = graph_utils.create_edge(
            t_v_node.vertex_id, t_v_switch.vertex_id, ELabel.CONTAINS + 'fail')
        e_host_to_node_not_in_graph = graph_utils.create_edge(
            t_v_node_not_in_graph.vertex_id, t_v_host.vertex_id, ELabel.ON)

        for v in [t_v_host_alarm, t_v_host, t_v_vm, t_v_vm_alarm,
                  t_v_switch, t_v_switch, t_v_node]:
            del(v[VProps.VITRAGE_ID])

        t.add_vertex(t_v_alarm_fail)
        mappings = ga.sub_graph_matching(t, [
            Mapping(t_v_host_alarm, host_alarm, True)], validate=True)
        self.assertEqual(
            0,
            len(mappings),
            'Template - Single vertex alarm not in graph '
            'Template_root is a specific host alarm ' + str(mappings))
        t.remove_vertex(t_v_alarm_fail)

        t.add_vertex(t_v_host_alarm)
        mappings = ga.sub_graph_matching(t, [
            Mapping(t_v_host_alarm, host_alarm, is_vertex=True)])
        self.assertEqual(
            1,
            len(mappings),
            'Template - Single vertex (host alarm) '
            'Template_root is a specific host alarm ' + str(mappings))

        t.add_vertex(t_v_host)
        mappings = ga.sub_graph_matching(t, [
            Mapping(t_v_host_alarm, host_alarm, is_vertex=True)])
        self.assertEqual(
            0,
            len(mappings),
            'Template - Two disconnected vertices (host alarm , host)'
            'Template_root is a specific host alarm ' + str(mappings))

        t.add_edge(e_alarm_on_host)
        mappings = ga.sub_graph_matching(t, [
            Mapping(t_v_host_alarm, host_alarm, is_vertex=True)])
        self.assertEqual(
            1, len(mappings),
            'Template - Two connected vertices (host alarm -ON-> host)'
            ' template_root is a specific host alarm ' + str(mappings))

        host = mappings[0][t_v_host.vertex_id]
        host_vertex = self.entity_graph.get_vertex(host.vertex_id)
        mappings = ga.sub_graph_matching(t, [
            Mapping(t_v_host, host_vertex, is_vertex=True)])
        self.assertEqual(
            ENTITY_GRAPH_ALARMS_PER_HOST,
            len(mappings),
            'Template - Two connected vertices (host alarm -ON-> host)'
            ' template_root is a specific host ' + str(mappings))

        t.add_vertex(t_v_vm)
        mappings = ga.sub_graph_matching(t, [
            Mapping(t_v_host_alarm, host_alarm, is_vertex=True)])
        self.assertEqual(
            0,
            len(mappings),
            'Template - Two connected vertices and a disconnected vertex'
            '(host alarm -ON-> host, instance)'
            ' template_root is a specific host alarm ' + str(mappings))

        t.add_vertex(t_v_vm_alarm)
        mappings = ga.sub_graph_matching(t, [
            Mapping(t_v_vm_alarm, vm_alarm, is_vertex=True)])
        self.assertEqual(
            0,
            len(mappings),
            'Template - Two connected vertices and two disconnected vertices'
            '(host alarm -ON-> host, instance, instance alarm)'
            ' template_root is a specific instance alarm ' + str(mappings))

        t.add_edge(e_alarm_on_vm)
        mappings = ga.sub_graph_matching(t, [
            Mapping(t_v_vm_alarm, vm_alarm, is_vertex=True)])
        self.assertEqual(
            0,
            len(mappings),
            'Template - Two connected vertices and two more connected vertices'
            '(host alarm -ON-> host, instance alarm -ON-> instance)'
            ' template_root is a specific instance alarm ' + str(mappings))

        t.add_edge(e_host_contains_vm)
        mappings = ga.sub_graph_matching(t, [
            Mapping(t_v_vm_alarm, vm_alarm, is_vertex=True)])
        self.assertEqual(
            ENTITY_GRAPH_ALARMS_PER_HOST,
            len(mappings),
            'Template - Four connected vertices'
            '(host alarm -ON-> host -CONTAINS-> instance <-ON- instance alarm)'
            ' template_root is a specific instance alarm ' + str(mappings))

        mappings = ga.sub_graph_matching(t, [
            Mapping(t_v_host_alarm, host_alarm, is_vertex=True)])
        self.assertEqual(
            ENTITY_GRAPH_VMS_PER_HOST * ENTITY_GRAPH_ALARMS_PER_VM,
            len(mappings),
            'Template - Four connected vertices'
            '(host alarm -ON-> host -CONTAINS-> instance <-ON- instance alarm)'
            ' template_root is a specific host alarm ' + str(mappings))

        mappings = ga.sub_graph_matching(t, [
            Mapping(t_v_host, host_vertex, is_vertex=True)])
        self.assertEqual(
            ENTITY_GRAPH_VMS_PER_HOST * ENTITY_GRAPH_ALARMS_PER_VM *
            ENTITY_GRAPH_ALARMS_PER_HOST,
            len(mappings),
            'Template - Four connected vertices'
            '(host alarm -ON-> host -CONTAINS-> instance <-ON- instance alarm)'
            ' template_root is a specific host ' + str(mappings))

        t.add_vertex(t_v_switch)
        mappings = ga.sub_graph_matching(t, [
            Mapping(t_v_vm_alarm, vm_alarm, is_vertex=True)])
        self.assertEqual(
            0,
            len(mappings),
            'Template - Four connected vertices and a disconnected vertex'
            '(host alarm -ON-> host -CONTAINS-> instance <-ON- instance alarm'
            ',switch) template_root is a instance alarm ' + str(mappings))

        t.add_edge(e_host_uses_switch)
        mappings = ga.sub_graph_matching(t, [
            Mapping(t_v_vm_alarm, vm_alarm, is_vertex=True)])
        self.assertEqual(
            ENTITY_GRAPH_ALARMS_PER_HOST,
            len(mappings),
            'Template - Five connected vertices'
            '(host alarm -ON-> host -CONTAINS-> instance <-ON- instance alarm'
            ',host -USES-> switch) template_root '
            'is a specific instance alarm ' + str(mappings))

        mappings = ga.sub_graph_matching(t, [
            Mapping(t_v_host, host_vertex, is_vertex=True)])
        self.assertEqual(
            ENTITY_GRAPH_VMS_PER_HOST * ENTITY_GRAPH_ALARMS_PER_VM *
            ENTITY_GRAPH_ALARMS_PER_HOST,
            len(mappings),
            'Template - Five connected vertices'
            '(host alarm -ON-> host -CONTAINS-> instance <-ON- instance alarm'
            ',host -USES-> switch) template_root is a specific host ' +
            str(mappings))

        mappings = ga.sub_graph_matching(t, [
            Mapping(t_v_switch, v_switch, is_vertex=True),
            Mapping(t_v_vm_alarm, vm_alarm, is_vertex=True)])
        self.assertEqual(
            ENTITY_GRAPH_ALARMS_PER_HOST,
            len(mappings),
            'Template - Five connected vertices, two mappings given'
            '(host alarm -ON-> host -CONTAINS-> instance <-ON- instance alarm'
            ',host -USES-> switch) template_root is a specific host ' +
            str(mappings))

        t.add_vertex(t_v_node_not_in_graph)
        t.add_edge(e_host_to_node_not_in_graph)
        mappings = ga.sub_graph_matching(t, [
            Mapping(t_v_vm_alarm, vm_alarm, is_vertex=True)])
        self.assertEqual(
            0,
            len(mappings),
            'Template - Five connected vertices and a invalid edge'
            '(host alarm -ON-> host -CONTAINS-> instance <-ON- instance alarm'
            ',host -USES-> switch) template_root is a instance alarm ' +
            str(mappings))
        t.remove_vertex(t_v_node_not_in_graph)

        t.remove_vertex(t_v_host_alarm)
        t.add_vertex(t_v_node)
        t.add_edge(e_node_contains_host)
        t.add_edge(e_node_contains_switch)
        mappings = ga.sub_graph_matching(t, [
            Mapping(t_v_vm_alarm, vm_alarm, is_vertex=True)])
        self.assertEqual(
            1,
            len(mappings),
            'Template - FIVE connected vertices'
            '(host -CONTAINS-> instance <-ON- instance alarm'
            ',node -CONTAINS-> host -USES-> switch, node-CONTAINS->switch)'
            ' template_root is a instance alarm ' + str(mappings))

        mappings = ga.sub_graph_matching(t, [
            Mapping(e_node_contains_switch, e_node_to_switch, is_vertex=False),
            Mapping(t_v_vm_alarm, vm_alarm, is_vertex=True)])
        self.assertEqual(
            1,
            len(mappings),
            'Template - FIVE connected vertices'
            '(host -CONTAINS-> instance <-ON- instance alarm'
            ',node -CONTAINS-> host -USES-> switch, node-CONTAINS->switch)'
            ' 3 Known Mappings[switch, node, vm alarm] ' + str(mappings))

        t.add_edge(e_node_contains_switch_fail)
        mappings = ga.sub_graph_matching(t, [
            Mapping(t_v_node, v_node, is_vertex=True),
            Mapping(t_v_switch, v_switch, is_vertex=True)], validate=True)
        self.assertEqual(
            0,
            len(mappings),
            'Template - FIVE connected vertices - 2 Known Mapping[node,switch]'
            ' Check that ALL edges between the 2 known mappings are checked'
            ' we now have node-CONTAINS fail->switch AND node-CONTAINS->switch'
            ' ')

        mappings = ga.sub_graph_matching(t, [
            Mapping(e_node_contains_switch,
                    e_node_to_switch, is_vertex=False)],
            validate=True
        )
        self.assertEqual(
            0,
            len(mappings),
            'Template - FIVE connected vertices - 2 Known Mapping[node,switch]'
            ' Check that ALL edges between the 2 known mappings are checked'
            ' we now have node-CONTAINS fail->switch AND node-CONTAINS->switch'
            ' ')

        t.remove_edge(e_node_contains_switch)
        mappings = ga.sub_graph_matching(t, [
            Mapping(t_v_node, v_node, is_vertex=True),
            Mapping(t_v_switch, v_switch, is_vertex=True)])
        self.assertEqual(
            0,
            len(mappings),
            'Template - FIVE connected vertices - 2 Known Mapping[node,switch]'
            ' But the edge between these 2 is not same as the graph '
            '(host -CONTAINS-> instance <-ON- instance alarm'
            ',node -CONTAINS-> host -USES-> switch, node-CONTAINS '
            'fail->switch)'
            ' ')

        mappings = ga.sub_graph_matching(t, [
            Mapping(t_v_vm_alarm, vm_alarm, is_vertex=True)])
        self.assertEqual(
            0,
            len(mappings),
            'Template - FIVE connected vertices'
            '(host -CONTAINS-> instance <-ON- instance alarm'
            ',node -CONTAINS-> host -USES-> switch, node-CONTAINS '
            'fail->switch)'
            ' template_root is a instance alarm')
