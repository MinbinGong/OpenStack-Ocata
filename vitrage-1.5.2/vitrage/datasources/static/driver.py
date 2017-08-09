# Copyright 2016 - Nokia, ZTE
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR  CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from itertools import chain
from six import iteritems
from six.moves import reduce

from oslo_log import log

from vitrage.common.constants import TopologyFields
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources.driver_base import DriverBase
from vitrage.datasources.static import STATIC_DATASOURCE
from vitrage.datasources.static import StaticFields
from vitrage.utils import file as file_utils

LOG = log.getLogger(__name__)


class StaticDriver(DriverBase):
    # base fields are required for all entities, others are treated as metadata
    BASE_FIELDS = {StaticFields.STATIC_ID, StaticFields.TYPE, VProps.ID}

    def __init__(self, conf):
        super(StaticDriver, self).__init__()
        self.cfg = conf

    @staticmethod
    def _is_valid_config(config):
        """check for validity of configuration"""
        # TODO(yujunz) check with yaml schema or reuse template validation
        return TopologyFields.DEFINITIONS in config

    @staticmethod
    def get_event_types():
        return []

    def enrich_event(self, event, event_type):
        pass

    def get_all(self, datasource_action):
        return self.make_pickleable(self._get_all_entities(),
                                    STATIC_DATASOURCE,
                                    datasource_action)

    def get_changes(self, datasource_action):
        return self.make_pickleable(self._get_changes_entities(),
                                    STATIC_DATASOURCE,
                                    datasource_action)

    def _get_all_entities(self):
        files = file_utils.list_files(self.cfg.static.directory, '.yaml', True)
        return reduce(chain, [self._get_entities_from_file(path)
                              for path in files], [])

    def _get_changes_entities(self):
        """TODO(yujunz): update from file change or CRUD"""
        return []

    @classmethod
    def _get_entities_from_file(cls, path):
        config = file_utils.load_yaml_file(path)

        if not cls._is_valid_config(config):
            LOG.warning("Skipped invalid config (possible obsoleted): {}"
                        .format(path))
            return []

        definitions = config[TopologyFields.DEFINITIONS]

        entities = definitions[TopologyFields.ENTITIES]
        relationships = definitions[TopologyFields.RELATIONSHIPS]

        return cls._pack(entities, relationships)

    @classmethod
    def _pack(cls, entities, relationships):
        entities_dict = {}
        for entity in entities:
            cls._pack_entity(entities_dict, entity)
        for rel in relationships:
            cls._pack_rel(entities_dict, rel)
        return entities_dict.values()

    @classmethod
    def _pack_entity(cls, entities_dict, entity):
        static_id = entity[StaticFields.STATIC_ID]
        if static_id not in entities_dict:
            metadata = {key: value for key, value in iteritems(entity)
                        if key not in cls.BASE_FIELDS}
            entities_dict[static_id] = entity
            entity[TopologyFields.RELATIONSHIPS] = []
            entity[TopologyFields.METADATA] = metadata
        else:
            LOG.warning("Skipped duplicated entity: {}".format(entity))

    @classmethod
    def _pack_rel(cls, entities_dict, rel):
        source_id = rel[TopologyFields.SOURCE]
        target_id = rel[TopologyFields.TARGET]

        if source_id == target_id:
            # self pointing relationship
            entities_dict[source_id][TopologyFields.RELATIONSHIPS].append(rel)
        else:
            source, target = entities_dict[source_id], entities_dict[target_id]
            source[TopologyFields.RELATIONSHIPS].append(
                cls._expand_neighbor(rel, target))

    @staticmethod
    def _expand_neighbor(rel, neighbor):
        """Expand config id to neighbor entity

        rel={'source': 's1', 'target': 'r1', 'relationship_type': 'attached'}
        neighbor={'static_id': 'h1', 'type': 'host.nova', 'id': 1}
        result={'relationship_type': 'attached', 'source': 's1',
                'target': {'static_id': 'h1', 'type': 'host.nova', 'id': 1}}
        """

        rel = rel.copy()
        if rel[StaticFields.SOURCE] == neighbor[StaticFields.STATIC_ID]:
            rel[StaticFields.SOURCE] = neighbor
        elif rel[StaticFields.TARGET] == neighbor[StaticFields.STATIC_ID]:
            rel[StaticFields.TARGET] = neighbor
        else:
            # TODO(yujunz) raise exception and ignore invalid relationship
            LOG.error("Invalid neighbor {} for relationship {}"
                      .format(neighbor, rel))
            return None
        return rel
