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
from oslo_log import log

from vitrage.api_handler.apis.base import ALARM_QUERY
from vitrage.api_handler.apis.base import ALARMS_ALL_QUERY
from vitrage.api_handler.apis.base import EntityGraphApisBase
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import VertexProperties as VProps


LOG = log.getLogger(__name__)


class AlarmApis(EntityGraphApisBase):

    def __init__(self, entity_graph, conf):
        self.entity_graph = entity_graph
        self.conf = conf

    def get_alarms(self, ctx, vitrage_id, all_tenants):
        LOG.debug("AlarmApis get_alarms - vitrage_id: %s, all_tenants=%s",
                  str(vitrage_id), all_tenants)

        project_id = ctx.get(self.TENANT_PROPERTY, None)
        is_admin_project = ctx.get(self.IS_ADMIN_PROJECT_PROPERTY, False)

        if not vitrage_id or vitrage_id == 'all':
            if all_tenants == "1":
                alarms = self.entity_graph.get_vertices(
                    query_dict=ALARMS_ALL_QUERY)
            else:
                alarms = self._get_alarms(project_id, is_admin_project)
                alarms += self._get_alarms_via_resource(project_id,
                                                        is_admin_project)
                alarms = set(alarms)
        else:
            alarms = self.entity_graph.neighbors(
                vitrage_id,
                vertex_attr_filter={VProps.CATEGORY: EntityCategory.ALARM,
                                    VProps.IS_DELETED: False})

        self._add_resource_details_to_alarms(alarms)

        return json.dumps({'alarms': [v.properties for v in alarms]})

    def _get_alarms(self, project_id, is_admin_project):
        """Finds all the alarms with project_id

        Finds all the alarms which has the project_id. In case the tenant is
        admin then project_id can also be None.

        :type project_id: string
        :type is_admin_project: boolean
        :rtype: list
        """

        alarm_query = self._get_query_with_project(EntityCategory.ALARM,
                                                   project_id,
                                                   is_admin_project)
        alarms = self.entity_graph.get_vertices(query_dict=alarm_query)
        return self._filter_alarms(alarms, project_id)

    def _get_alarms_via_resource(self, project_id, is_admin_project):
        """Finds all the alarms with project_id on their resource

        Finds all the resource which has project_id and return all the alarms
        on those resources project_id. In case the tenant is admin then
        project_id can also be None.

        :type project_id: string
        :type is_admin_project: boolean
        :rtype: list
        """

        resource_query = self._get_query_with_project(EntityCategory.RESOURCE,
                                                      project_id,
                                                      is_admin_project)

        alarms = []
        resources = self.entity_graph.get_vertices(query_dict=resource_query)

        for resource in resources:
            new_alarms = \
                self.entity_graph.neighbors(
                    resource.vertex_id, vertex_attr_filter=ALARM_QUERY)
            alarms = alarms + new_alarms

        return alarms
