# Copyright 2016 - Alcatel-Lucent
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,  software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND,  either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo_log import log

from vitrage.common.constants import DatasourceAction
from vitrage.common.constants import DatasourceProperties as DSProps
from vitrage.datasources.alarm_driver_base import AlarmDriverBase
from vitrage.datasources.aodh import AODH_DATASOURCE
from vitrage.datasources.aodh.properties import AodhEventType
from vitrage.datasources.aodh.properties import AodhProperties as AodhProps
from vitrage.datasources.aodh.properties import AodhState
from vitrage import os_clients
from vitrage.utils import datetime as datetime_utils

LOG = log.getLogger(__name__)


class AodhDriver(AlarmDriverBase):

    def __init__(self, conf):
        super(AodhDriver, self).__init__()
        self._client = None
        self.conf = conf
        self._init_aodh_event_actions()
        self._cache_all_alarms()

    @property
    def client(self):
        if not self._client:
            self._client = os_clients.ceilometer_client(self.conf)
        return self._client

    def _entity_type(self):
        return AODH_DATASOURCE

    def _alarm_key(self, alarm):
        return alarm[AodhProps.ALARM_ID]

    def _cache_all_alarms(self):
        alarms = self._get_alarms()
        self._filter_and_cache_alarms(alarms,
                                      self._filter_get_valid)

    def _get_alarms(self):
        try:
            aodh_alarms = self.client.alarms.list()
            return [self._convert_alarm(alarm) for alarm in aodh_alarms]
        except Exception as e:
            LOG.exception("Failed to get all alarms, Exception: %s", e)
        return []

    def _is_erroneous(self, alarm):
        return alarm and alarm[AodhProps.STATE] == AodhState.ALARM

    def _status_changed(self, alarm1, alarm2):
        return alarm1 and alarm2 and \
            not alarm1[AodhProps.STATE] == alarm2[AodhProps.STATE]

    def _is_valid(self, alarm):
        return True

    @classmethod
    def _convert_event_alarm(cls, alarm):
        res = cls._convert_base_alarm(alarm)
        res[AodhProps.EVENT_TYPE] = alarm.event_rule[AodhProps.EVENT_TYPE],
        res[AodhProps.RESOURCE_ID] = _parse_query(alarm.event_rule,
                                                  AodhProps.EVENT_RESOURCE_ID)
        return res

    @classmethod
    def _convert_threshold_alarm(cls, alarm):
        res = cls._convert_base_alarm(alarm)
        res[AodhProps.STATE_TIMESTAMP] = alarm.state_timestamp
        res[AodhProps.RESOURCE_ID] = _parse_query(alarm.threshold_rule,
                                                  AodhProps.RESOURCE_ID)
        return res

    @classmethod
    def _convert_vitrage_alarm(cls, alarm):
        res = cls._convert_base_alarm(alarm)
        res[AodhProps.VITRAGE_ID] = _parse_query(alarm.event_rule,
                                                 AodhProps.VITRAGE_ID)
        res[AodhProps.RESOURCE_ID] = _parse_query(alarm.event_rule,
                                                  AodhProps.RESOURCE_ID)
        return res

    @staticmethod
    def _convert_base_alarm(alarm):
        # TODO(iafek): what if the alarm state is 'insufficient data'

        return {
            AodhProps.DESCRIPTION: alarm.description,
            AodhProps.ENABLED: alarm.enabled,
            AodhProps.ALARM_ID: alarm.alarm_id,
            AodhProps.NAME: alarm.name,
            AodhProps.PROJECT_ID: alarm.project_id,
            AodhProps.REPEAT_ACTIONS: alarm.repeat_actions,
            AodhProps.SEVERITY: alarm.severity,
            AodhProps.STATE: alarm.state,
            AodhProps.TIMESTAMP: alarm.timestamp,
            AodhProps.TYPE: alarm.type
        }

    @classmethod
    def _convert_alarm(cls, alarm):
        alarm_type = alarm.type
        if alarm_type == AodhProps.EVENT and \
            _is_vitrage_alarm(alarm.event_rule):
            return cls._convert_vitrage_alarm(alarm)
        elif alarm_type == AodhProps.EVENT:
            return cls._convert_event_alarm(alarm)
        elif alarm_type == AodhProps.THRESHOLD:
            return cls._convert_threshold_alarm(alarm)
        else:
            LOG.warning('Unsupported Aodh alarm of type %s' % alarm_type)

    @staticmethod
    def get_event_types():
        # Add event_types to receive notifications about
        return [AodhEventType.CREATION,
                AodhEventType.STATE_TRANSITION,
                AodhEventType.RULE_CHANGE,
                AodhEventType.DELETION]

    def enrich_event(self, event, event_type):
        if event_type in self.actions:
            entity = self.actions[event_type](event)
        else:
            LOG.warning('Unsupported Aodh event type %s' % event_type)
            return None

        # Don't need to update entity, only update the cache
        if entity is None:
            return None

        entity[DSProps.EVENT_TYPE] = event_type

        return AodhDriver.make_pickleable([entity],
                                          AODH_DATASOURCE,
                                          DatasourceAction.UPDATE)[0]

    def _init_aodh_event_actions(self):
        self.actions = {
            AodhEventType.CREATION: self._convert_alarm_creation_event,
            AodhEventType.RULE_CHANGE: self._convert_alarm_rule_change_event,
            AodhEventType.STATE_TRANSITION:
                self._convert_alarm_state_transition_event,
            AodhEventType.DELETION: self._convert_alarm_deletion_event
        }

    @classmethod
    def _convert_base_event(cls, event):
        return {
            AodhProps.PROJECT_ID: event[AodhProps.PROJECT_ID],
            AodhProps.ALARM_ID: event[AodhProps.ALARM_ID],
            AodhProps.SEVERITY: event[AodhProps.SEVERITY],
            AodhProps.TIMESTAMP: event[AodhProps.TIMESTAMP],
        }

    @classmethod
    def _convert_vitrage_alarm_event(cls, rule):
        return {
            AodhProps.VITRAGE_ID: _parse_query(rule, AodhProps.VITRAGE_ID),
            AodhProps.RESOURCE_ID: _parse_query(rule, AodhProps.RESOURCE_ID)
        }

    @classmethod
    def _convert_threshold_alarm_event(cls, event):
        rule = event[AodhProps.DETAIL][AodhProps.RULE]
        return {
            AodhProps.RESOURCE_ID: _parse_query(rule, AodhProps.RESOURCE_ID),
            AodhProps.STATE_TIMESTAMP: event[AodhProps.STATE_TIMESTAMP]
        }

    @classmethod
    def _convert_event_alarm_event(cls, rule):
        return {
            AodhProps.EVENT_TYPE: rule[AodhProps.EVENT_TYPE],
            AodhProps.RESOURCE_ID:
                _parse_query(rule, AodhProps.EVENT_RESOURCE_ID)
        }

    @classmethod
    def _convert_detail_event(cls, event):
        alarm_info = event[AodhProps.DETAIL]
        alarm_rule = alarm_info[AodhProps.RULE]

        entity_detail = {
            AodhProps.DESCRIPTION: alarm_info[AodhProps.DESCRIPTION],
            AodhProps.ENABLED: alarm_info[AodhProps.ENABLED],
            AodhProps.NAME: alarm_info[AodhProps.NAME],
            AodhProps.STATE: alarm_info[AodhProps.STATE],
            AodhProps.REPEAT_ACTIONS: alarm_info[AodhProps.REPEAT_ACTIONS],
            AodhProps.TYPE: alarm_info[AodhProps.TYPE]
        }

        if _is_vitrage_alarm(alarm_rule):
            entity_detail.update(cls._convert_vitrage_alarm_event(alarm_rule))
        elif entity_detail[AodhProps.TYPE] == AodhProps.EVENT:
            entity_detail.update(cls._convert_event_alarm_event(alarm_rule))
        elif entity_detail[AodhProps.TYPE] == AodhProps.THRESHOLD:
            entity_detail.update(
                cls._convert_threshold_alarm_event(event))

        return entity_detail

    @classmethod
    def _parse_changed_rule(cls, change_rule):
        entity = {}
        if AodhProps.EVENT_TYPE in change_rule:
            entity[AodhProps.EVENT_TYPE] = change_rule[AodhProps.EVENT_TYPE]
        if 'query' in change_rule:
            event_resource_id = \
                _parse_query(change_rule, AodhProps.EVENT_RESOURCE_ID)
            resource_id = \
                _parse_query(change_rule, AodhProps.RESOURCE_ID)
            if event_resource_id or resource_id:
                entity[AodhProps.RESOURCE_ID] = event_resource_id if \
                    event_resource_id is not None else resource_id

        return entity

    def _convert_alarm_creation_event(self, event):
        entity = self._convert_base_event(event)
        detail = self._convert_detail_event(event)
        entity.update(detail)

        return self._filter_and_cache_alarm(entity, None,
                                            self._filter_get_erroneous,
                                            datetime_utils.utcnow(False))

    def _convert_alarm_rule_change_event(self, event):
        """handle alarm rule change notification

        example of changed rule:
        "detail": {"severity": "critical",
                   "rule":
                       {"query": [{"field": "traits.resource_id",
                                   "type": "",
                                   "value": "1",
                                   "op": "eq"}],
                       "event_type": "instance.update"}}
        """

        old_alarm = self._old_alarm(event)
        entity = old_alarm.copy()

        changed_rule = event[AodhProps.DETAIL]
        for (changed_type, changed_info) in changed_rule.items():
            # handle changed rule which may effect the neighbor
            if changed_type == AodhProps.RULE:
                entity.update(self._parse_changed_rule(
                    changed_rule[changed_type]))
            # handle other changed alarm properties
            elif changed_type in AodhProps.__dict__.values():
                entity[changed_type] = changed_info

        return self._filter_and_cache_alarm(entity, old_alarm,
                                            self._filter_get_erroneous,
                                            datetime_utils.utcnow(False))

    def _convert_alarm_state_transition_event(self, event):
        old_alarm = self._old_alarm(event)
        entity = old_alarm.copy()
        entity[AodhProps.STATE] = event[AodhProps.DETAIL][AodhProps.STATE]

        return self._filter_and_cache_alarm(entity, old_alarm,
                                            self._filter_get_change,
                                            datetime_utils.utcnow(False))

    def _convert_alarm_deletion_event(self, event):
        alarm_key = self._alarm_key(event)
        alarm = self.cache.pop(alarm_key)[0]
        return alarm if self._is_erroneous(alarm) else None


def _parse_query(data, key):
    query_fields = data.get(AodhProps.QUERY, {})
    for query in query_fields:
        field = query['field']
        if field == key:
            return query['value']
    return None


def _is_vitrage_alarm(rule):
    return _parse_query(rule, AodhProps.VITRAGE_ID) is not None
