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

from vitrage.common.constants import VertexProperties as VProps
from vitrage.evaluator.template_fields import TemplateFields


class BaselineTools(object):
    @staticmethod
    def get_score(action_info):
        return 1  # no priorities

    @staticmethod
    def get_key(action_specs):
        target_ids = {k: v.vertex_id for k, v in action_specs.targets.items()}
        return action_specs.type, hash(tuple(sorted(target_ids.items())))


class RaiseAlarmTools(object):

    def __init__(self, scores):
        self.scores = scores

    def get_score(self, action_info):
        severity = action_info.specs.properties[TemplateFields.SEVERITY]
        return self.scores.get(severity.upper(), 0)

    @staticmethod
    def get_key(action_specs):
        return action_specs.type,\
            action_specs.properties[TemplateFields.ALARM_NAME], \
            hash(action_specs.targets[TemplateFields.TARGET].vertex_id)


class SetStateTools(object):

    def __init__(self, scores):
        self.scores = scores

    def get_score(self, action_info):
        state = action_info.specs.properties[TemplateFields.STATE].upper()
        target_resource = action_info.specs.targets[TemplateFields.TARGET]
        return self.scores[target_resource[VProps.TYPE]].get(state, 0)

    @staticmethod
    def get_key(action_specs):
        return action_specs.type, \
            hash(action_specs.targets[TemplateFields.TARGET].vertex_id)
