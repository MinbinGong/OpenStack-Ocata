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

from oslo_log import log

from vitrage.api_handler.apis.base import ALARMS_ALL_QUERY
from vitrage.api_handler.apis.base import EDGE_QUERY
from vitrage.api_handler.apis.base import EntityGraphApisBase
from vitrage.api_handler.apis.base import TOPOLOGY_AND_ALARMS_QUERY
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources.nova.instance import NOVA_INSTANCE_DATASOURCE
from vitrage.datasources import OPENSTACK_CLUSTER
from vitrage.datasources.transformer_base import build_key
from vitrage.datasources.transformer_base import CLUSTER_ID


LOG = log.getLogger(__name__)


class TopologyApis(EntityGraphApisBase):

    def __init__(self, entity_graph, conf):
        self.entity_graph = entity_graph
        self.conf = conf

    def get_topology(self, ctx, graph_type, depth, query, root, all_tenants):
        LOG.debug("TopologyApis get_topology - root: %s, all_tenants=%s",
                  str(root), all_tenants)

        project_id = ctx.get(self.TENANT_PROPERTY, None)
        is_admin_project = ctx.get(self.IS_ADMIN_PROJECT_PROPERTY, False)
        ga = self.entity_graph.algo

        if graph_type == 'tree':
            if not query:
                LOG.error("Graph-type 'tree' requires a filter.")
                raise Exception("Graph-type 'tree' requires a filter.")

            current_query = query
            if not all_tenants:
                project_query = \
                    {'or': [{'==': {VProps.PROJECT_ID: project_id}},
                            {'==': {VProps.PROJECT_ID: None}}]}
                current_query = {'and': [query, project_query]}

            graph = ga.graph_query_vertices(query_dict=current_query,
                                            root_id=root,
                                            depth=depth,
                                            edge_query_dict=EDGE_QUERY)
        # By default the graph_type is 'graph'
        else:
            if all_tenants:
                q = query if query else TOPOLOGY_AND_ALARMS_QUERY
                graph = ga.create_graph_from_matching_vertices(
                    query_dict=q,
                    edge_attr_filter={VProps.IS_DELETED: False})
            else:
                graph = self._get_topology_for_specific_project(
                    ga,
                    query,
                    project_id,
                    is_admin_project,
                    root)

            alarms = graph.get_vertices(query_dict=ALARMS_ALL_QUERY)
            self._add_resource_details_to_alarms(alarms)
            graph.update_vertices(alarms)

        return graph.json_output_graph()

    def _get_topology_for_specific_project(self,
                                           ga,
                                           query,
                                           project_id,
                                           is_admin_project,
                                           root):
        """Finds the topology in consideration with the project_id

        Finds all the entities which has project_id. In case the tenant is
        admin then project_id can also be None.

        :type ga: NXAlgorithm
        :type query: dictionary
        :type project_id: string
        :type is_admin_project: boolean
        :type root: string
        :rtype: NXGraph
        """

        if query:
            q = query
        else:
            alarm_query = self._get_query_with_project(EntityCategory.ALARM,
                                                       project_id,
                                                       is_admin=True)

            resource_query = \
                self._get_query_with_project(EntityCategory.RESOURCE,
                                             project_id,
                                             is_admin_project)

            default_query = {'or': [resource_query, alarm_query]}
            q = default_query

        tmp_graph = ga.create_graph_from_matching_vertices(
            query_dict=q,
            edge_attr_filter={VProps.IS_DELETED: False})
        graph = ga.subgraph(self._topology_for_unrooted_graph(ga,
                                                              tmp_graph,
                                                              root))
        self._remove_alarms_of_other_projects(graph,
                                              project_id,
                                              is_admin_project)

        return graph

    def _remove_alarms_of_other_projects(self,
                                         graph,
                                         current_project_id,
                                         is_admin_project):
        """Removes wrong alarms from the graph

        Removes alarms of other tenants from the graph, In case the tenant is
        admin then project_id can also be None.

        :type graph: NXGraph
        :type current_project_id: string
        :type is_admin_project: boolean
        """

        for alarm in graph.get_vertices(query_dict=ALARMS_ALL_QUERY):
            if not alarm.get(VProps.PROJECT_ID, None):
                cat_filter = {VProps.CATEGORY: EntityCategory.RESOURCE}
                resource_neighbors = \
                    self.entity_graph.neighbors(alarm.vertex_id,
                                                vertex_attr_filter=cat_filter)
                if len(resource_neighbors) > 0:
                    resource_proj_id = \
                        resource_neighbors[0].get(VProps.PROJECT_ID, None)
                    cond1 = is_admin_project and resource_proj_id and \
                        resource_proj_id != current_project_id
                    cond2 = not is_admin_project and \
                        (not resource_proj_id or
                         resource_proj_id != current_project_id)
                    if cond1 or cond2:
                        graph.remove_vertex(alarm)

    def _topology_for_unrooted_graph(self, ga, subgraph, root):
        """Finds topology for unrooted subgraph

        1. Finds all the connected component subgraphs in subgraph.
        2. For each component, finds the path from one of the VMs (if exists)
           to the root entity.
        3. Unify all the entities found and return them

        :type ga: NXAlgorithm
        :type subgraph: networkx graph
        :type root: string
        :rtype: list
        """

        entities = []

        if not root:
            root = build_key([EntityCategory.RESOURCE,
                              OPENSTACK_CLUSTER,
                              CLUSTER_ID])

        root_vertex = \
            self.entity_graph.get_vertex(root)
        local_connected_component_subgraphs = \
            ga.connected_component_subgraphs(subgraph)

        for component_subgraph in local_connected_component_subgraphs:
            entities += component_subgraph.nodes()
            instance_in_component_subgraph = \
                self._find_instance_in_graph(component_subgraph)
            if instance_in_component_subgraph:
                paths = ga.all_simple_paths(root_vertex.vertex_id,
                                            instance_in_component_subgraph)
                for path in paths:
                    entities += path

        return set(entities)

    @staticmethod
    def _find_instance_in_graph(graph):
        for node, node_data in graph.nodes_iter(data=True):
            if node_data[VProps.CATEGORY] == EntityCategory.RESOURCE and \
                    node_data[VProps.TYPE] == NOVA_INSTANCE_DATASOURCE:
                return node
        return None
