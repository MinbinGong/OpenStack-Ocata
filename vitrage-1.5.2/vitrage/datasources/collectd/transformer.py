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

from oslo_log import log as logging

from vitrage.common.constants import DatasourceProperties as DSProps
from vitrage.common.constants import EdgeLabel
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources.alarm_properties import AlarmProperties as AlarmProps
from vitrage.datasources.alarm_transformer_base import AlarmTransformerBase
from vitrage.datasources.collectd import COLLECTD_DATASOURCE
from vitrage.datasources.collectd.properties import\
    CollectdProperties as CProps
from vitrage.datasources import transformer_base as tbase
import vitrage.graph.utils as graph_utils
from vitrage.utils.datetime import format_unix_timestamp

LOG = logging.getLogger(__name__)


class CollectdTransformer(AlarmTransformerBase):

    def __init__(self, transformers, conf):
        super(CollectdTransformer, self).__init__(transformers, conf)

    def _create_snapshot_entity_vertex(self, entity_event):
        # The Collectd datasource does not support snapshot mode
        return None

    def _create_update_entity_vertex(self, entity_event):
        return self._create_vertex(entity_event)

    def _create_vertex(self, entity_event):

        entity_event['timestamp'] = format_unix_timestamp(
            entity_event[CProps.TIME], tbase.TIMESTAMP_FORMAT)

        update_timestamp = entity_event['timestamp']

        sample_timestamp = entity_event[DSProps.SAMPLE_DATE]

        entity_state = AlarmProps.INACTIVE_STATE \
            if self._ok_status(entity_event) else AlarmProps.ACTIVE_STATE

        metadata = {
            VProps.NAME: entity_event[CProps.MESSAGE],
            VProps.SEVERITY: entity_event[CProps.SEVERITY],
            VProps.RAWTEXT: self.generate_raw_text(entity_event)
        }

        return graph_utils.create_vertex(
            self._create_entity_key(entity_event),
            entity_category=EntityCategory.ALARM,
            entity_type=entity_event[DSProps.ENTITY_TYPE],
            entity_state=entity_state,
            sample_timestamp=sample_timestamp,
            update_timestamp=update_timestamp,
            metadata=metadata)

    def _create_snapshot_neighbors(self, entity_event):
        return self._create_collectd_neighbors(entity_event)

    def _create_update_neighbors(self, entity_event):
        return self._create_collectd_neighbors(entity_event)

    def _create_collectd_neighbors(self, entity_event):

        resource_type = entity_event[CProps.RESOURCE_TYPE]
        if resource_type:
            return [self._create_neighbor(
                entity_event,
                entity_event[CProps.RESOURCE_NAME],
                resource_type,
                EdgeLabel.ON,
                neighbor_category=EntityCategory.RESOURCE)]

        return []

    def _ok_status(self, entity_event):
        return entity_event[CProps.SEVERITY] == 'OK'

    def _create_entity_key(self, entity_event):

        entity_type = entity_event[DSProps.ENTITY_TYPE]
        alarm_id = entity_event[CProps.ID]
        resource_name = entity_event[CProps.RESOURCE_NAME]
        return tbase.build_key(self._key_values(entity_type,
                                                resource_name,
                                                alarm_id))

    def get_type(self):
        return COLLECTD_DATASOURCE

    @staticmethod
    def generate_raw_text(entity_event):
        resources = [entity_event.get(CProps.TYPE_INSTANCE),
                     entity_event[CProps.PLUGIN],
                     entity_event.get(CProps.PLUGIN_INSTANCE)]
        return '-'.join([resource for resource in resources if resource])
