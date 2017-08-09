# Copyright 2016 - Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from vitrage.common.constants import EdgeLabel
from vitrage.common.constants import EntityCategory
from vitrage.evaluator.actions.base import action_types

status_msgs = {

    # General 1-19
    0: 'Template validation is OK',
    1: 'template_id field contains incorrect string value.',
    2: 'Duplicate template_id definition.',
    3: 'template_id does not appear in the definition block.',
    4: 'Syntax error: ',

    # definitions section 20-39
    20: 'definitions section must contain entities field.',
    21: 'definitions section is a mandatory section.',

    # Entities status messages 40-59
    41: 'Entity definition must contain template_id field.',
    42: 'Entity definition must contain category field.',
    43: 'At least one entity must be defined.',
    45: 'Invalid entity category. Category must be from types: '
        '{categories}'.format(categories=EntityCategory.categories()),
    46: 'Entity field is required.',

    # metadata section status messages 60-79
    60: 'metadata section must contain id field.',
    62: 'metadata is a mandatory section.',

    # scenarios section status messages 80-99
    80: 'scenarios is a mandatory section.',
    81: 'At least one scenario must be defined.',
    82: 'scenario field is required.',
    83: 'Entity definition must contain condition field.',
    84: 'Entity definition must contain actions field.',
    85: 'Failed to convert condition.',

    # relationships status messages 100-119
    100: 'Invalid relation type. Relation type must be from types: '
         '{labels}'.format(labels=EdgeLabel.labels()),
    101: 'Relationship field is required.',
    102: 'Relationship definition must contain source field.',
    103: 'Relationship definition must contain target field.',
    104: 'Relationship definition must contain template_id field.',

    # actions status messages 120-139
    120: 'Invalid action type. Action type must be from types: '
         '{actions}'.format(actions=action_types),
    121: 'At least one action must be defined.',
    122: 'Action field is required.',
    123: 'Relationship definition must contain action_type field.',
    124: 'Relationship definition must contain action_target field.',
    125: 'raise_alarm action must contain alarm_name field in properties '
         'block.',
    126: 'raise_alarm action must contain severity field in properties block.',
    127: 'raise_alarm action must contain target field in target_action block',
    128: 'set_state action must contain state field in properties block.',
    129: 'set_state action must contain target field in target_action block.',
    130: 'add_causal_relationship action must contain target and source field '
         'in target_action block.',
    131: 'mark_down action must contain \'target\' field in'
         ' \'target_action\' block.',
    132: 'add_causal_relationship action requires action_target to be ALARM'

}
