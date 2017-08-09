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

from vitrage.common.constants import EdgeProperties as EConst
from vitrage.common.constants import VertexProperties as VConst
from vitrage.graph.driver.elements import Edge
from vitrage.graph.driver.elements import Vertex


def create_vertex(vitrage_id,
                  entity_id=None,
                  entity_category=None,
                  entity_type=None,
                  entity_state=None,
                  is_deleted=False,
                  sample_timestamp=None,
                  update_timestamp=None,
                  is_placeholder=False,
                  project_id=None,
                  metadata=None):
    """A builder to create a vertex

    :param vitrage_id:
    :type vitrage_id: str
    :param entity_id:
    :type entity_id: str
    :param entity_category:
    :type entity_category: str
    :param entity_type:
    :type entity_type: str
    :param entity_state:
    :type entity_state: str
    :param is_deleted:
    :type is_deleted: boolean
    :param update_timestamp:
    :type update_timestamp: str
    :param sample_timestamp:
    :type sample_timestamp: str
    :param metadata:
    :type metadata: dict
    :param is_placeholder:
    :type is_placeholder: boolean
    :param project_id:
    :type project_id: str
    :return:
    :rtype: Vertex
    """

    properties = {
        VConst.ID: entity_id,
        VConst.STATE: entity_state,
        VConst.TYPE: entity_type,
        VConst.CATEGORY: entity_category,
        VConst.IS_DELETED: is_deleted,
        VConst.UPDATE_TIMESTAMP: update_timestamp,
        VConst.SAMPLE_TIMESTAMP: sample_timestamp,
        VConst.IS_PLACEHOLDER: is_placeholder,
        VConst.VITRAGE_ID: vitrage_id,
        VConst.PROJECT_ID: project_id
    }
    if metadata:
        properties.update(metadata)
    properties = dict(
        (k, v) for k, v in properties.items() if v is not None)
    vertex = Vertex(vertex_id=vitrage_id, properties=properties)
    return vertex


def create_edge(source_id,
                target_id,
                relationship_type,
                is_deleted=False,
                update_timestamp=None,
                metadata=None):
    """A builder to create an edge

    :param update_timestamp:
    :param source_id:
    :type source_id: str
    :param target_id:
    :type target_id: str
    :param relationship_type:
    :type relationship_type: str
    :param is_deleted:
    :type is_deleted: str
    :param metadata:
    :type metadata: dict
    :return:
    :rtype: Edge
    """
    properties = {
        EConst.UPDATE_TIMESTAMP: update_timestamp,
        EConst.IS_DELETED: is_deleted,
        EConst.RELATIONSHIP_TYPE: relationship_type,
    }
    if metadata:
        properties.update(metadata)
    properties = dict(
        (k, v) for k, v in properties.items() if v is not None)
    edge = Edge(source_id=source_id,
                target_id=target_id,
                label=relationship_type,
                properties=properties)
    return edge
