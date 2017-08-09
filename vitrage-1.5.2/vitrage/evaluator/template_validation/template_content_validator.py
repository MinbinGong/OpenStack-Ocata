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

from oslo_log import log
from six.moves import reduce
from vitrage.common.constants import EntityCategory
from vitrage.evaluator.actions.base import ActionType
from vitrage.evaluator.template_data import TemplateData
from vitrage.evaluator.template_fields import TemplateFields
from vitrage.evaluator.template_validation.base import get_correct_result
from vitrage.evaluator.template_validation.base import get_fault_result
from vitrage.evaluator.template_validation.status_messages import status_msgs

LOG = log.getLogger(__name__)


RESULT_DESCRIPTION = 'Template content validation'


def content_validation(template):

    template_definitions = template[TemplateFields.DEFINITIONS]

    entities_index = {}
    entities = template_definitions[TemplateFields.ENTITIES]
    result = validate_entities_definition(entities, entities_index)

    relationships_index = {}

    if result.is_valid_config and \
       TemplateFields.RELATIONSHIPS in template_definitions:

        relationships = template_definitions[TemplateFields.RELATIONSHIPS]
        result = validate_relationships_definitions(relationships,
                                                    relationships_index,
                                                    entities_index)
    if result.is_valid_config:
        scenarios = template[TemplateFields.SCENARIOS]
        definitions_index = entities_index.copy()
        definitions_index.update(relationships_index)
        result = validate_scenarios(scenarios, definitions_index)

    return result


def validate_entities_definition(entities, entities_index):

    for entity in entities:

        entity_dict = entity[TemplateFields.ENTITY]
        result = validate_entity_definition(entity_dict, entities_index)

        if not result.is_valid_config:
            return result

        entities_index[entity_dict[TemplateFields.TEMPLATE_ID]] = entity_dict

    return get_correct_result(RESULT_DESCRIPTION)


def validate_entity_definition(entity_dict, entities_index):

    template_id = entity_dict[TemplateFields.TEMPLATE_ID]
    if template_id in entities_index:
        LOG.error('%s status code: %s' % (status_msgs[2], 2))
        return get_fault_result(RESULT_DESCRIPTION, 2)

    return get_correct_result(RESULT_DESCRIPTION)


def validate_relationships_definitions(relationships,
                                       relationships_index,
                                       entities_index):

    for relationship in relationships:

        relationship_dict = relationship[TemplateFields.RELATIONSHIP]
        result = validate_relationship(relationship_dict,
                                       relationships_index,
                                       entities_index)
        if not result.is_valid_config:
            return result

        template_id = relationship_dict[TemplateFields.TEMPLATE_ID]
        relationships_index[template_id] = relationship_dict
    return get_correct_result(RESULT_DESCRIPTION)


def validate_relationship(relationship, relationships_index, entities_index):

    template_id = relationship[TemplateFields.TEMPLATE_ID]
    if template_id in relationships_index or template_id in entities_index:
        LOG.error('%s status code: %s' % (status_msgs[2], 2))
        return get_fault_result(RESULT_DESCRIPTION, 2)

    target = relationship[TemplateFields.TARGET]
    result = _validate_template_id(entities_index, target)

    if result.is_valid_config:
        source = relationship[TemplateFields.SOURCE]
        result = _validate_template_id(entities_index, source)

    return result


def validate_scenarios(scenarios, definitions_index):

    for scenario in scenarios:

        scenario_values = scenario[TemplateFields.SCENARIO]

        condition = scenario_values[TemplateFields.CONDITION]
        result = validate_scenario_condition(condition, definitions_index)

        if not result.is_valid_config:
            return result

        actions = scenario_values[TemplateFields.ACTIONS]
        result = validate_scenario_actions(actions, definitions_index)

        if not result.is_valid_config:
            return result

    return get_correct_result(RESULT_DESCRIPTION)


def validate_scenario_condition(condition, definitions_index):

    try:
        TemplateData.convert_to_dnf_format(condition)
    except Exception:
        LOG.error('%s status code: %s' % (status_msgs[85], 85))
        return get_fault_result(RESULT_DESCRIPTION, 85)

    values_to_replace = ' and ', ' or ', ' not ', '(', ')'
    condition = reduce(lambda cond, v: cond.replace(v, ' '),
                       values_to_replace,
                       condition)

    for condition_var in condition.split(' '):

        if len(condition_var.strip()) == 0:
            continue

        result = _validate_template_id(definitions_index, condition_var)
        if not result.is_valid_config:
            return result

    return get_correct_result(RESULT_DESCRIPTION)


def validate_scenario_actions(actions, definitions_index):

    for action in actions:
        result = validate_scenario_action(action[TemplateFields.ACTION],
                                          definitions_index)
        if not result.is_valid_config:
            return result

    return get_correct_result(RESULT_DESCRIPTION)


def validate_scenario_action(action, definitions_index):

    action_type = action[TemplateFields.ACTION_TYPE]
    actions = {
        ActionType.RAISE_ALARM: validate_raise_alarm_action,
        ActionType.SET_STATE: validate_set_state_action,
        ActionType.ADD_CAUSAL_RELATIONSHIP:
        validate_add_causal_relationship_action,
        ActionType.MARK_DOWN: validate_mark_down_action,
    }

    if action_type not in actions.keys():
        LOG.error('%s status code: %s' % (status_msgs[120], 120))
        return get_fault_result(RESULT_DESCRIPTION, 120)

    return actions[action_type](action, definitions_index)


def validate_raise_alarm_action(action, definitions_index):

    properties = action[TemplateFields.PROPERTIES]

    if TemplateFields.ALARM_NAME not in properties:
        LOG.error('%s status code: %s' % (status_msgs[125], 125))
        return get_fault_result(RESULT_DESCRIPTION, 125)

    if TemplateFields.SEVERITY not in properties:
        LOG.error('%s status code: %s' % (status_msgs[126], 126))
        return get_fault_result(RESULT_DESCRIPTION, 126)

    action_target = action[TemplateFields.ACTION_TARGET]
    if TemplateFields.TARGET not in action_target:
        LOG.error('%s status code: %s' % (status_msgs[127], 127))
        return get_fault_result(RESULT_DESCRIPTION, 127)

    target = action_target[TemplateFields.TARGET]
    return _validate_template_id(definitions_index, target)


def validate_set_state_action(action, definitions_index):

    properties = action[TemplateFields.PROPERTIES]

    if TemplateFields.STATE not in properties:
        LOG.error('%s status code: %s' % (status_msgs[128], 128))
        return get_fault_result(RESULT_DESCRIPTION, 128)

    action_target = action[TemplateFields.ACTION_TARGET]
    if TemplateFields.TARGET not in action_target:
        LOG.error('%s status code: %s' % (status_msgs[129], 129))
        return get_fault_result(RESULT_DESCRIPTION, 129)

    target = action_target[TemplateFields.TARGET]
    return _validate_template_id(definitions_index, target)


def validate_add_causal_relationship_action(action, definitions_index):

    action_target = action[TemplateFields.ACTION_TARGET]

    for key in [TemplateFields.TARGET, TemplateFields.SOURCE]:
        if key not in action_target:
            LOG.error('%s status code: %s' % (status_msgs[130], 130))
            return get_fault_result(RESULT_DESCRIPTION, 130)

        template_id = action_target[key]
        result = _validate_template_id(definitions_index, template_id)

        if not result.is_valid_config:
            return result

        entity = definitions_index[template_id]
        result = _validate_entity_category(entity, EntityCategory.ALARM)
        if not result.is_valid_config:
            return result

    return get_correct_result(RESULT_DESCRIPTION)


def validate_mark_down_action(action, definitions_index):

    action_target = action[TemplateFields.ACTION_TARGET]
    if TemplateFields.TARGET not in action_target:
        LOG.error('%s status code: %s' % (status_msgs[131], 131))
        return get_fault_result(RESULT_DESCRIPTION, 131)

    target = action_target[TemplateFields.TARGET]
    return _validate_template_id(definitions_index, target)


def _validate_template_id(definitions_index, id_to_check):

    if id_to_check not in definitions_index:
        msg = status_msgs[3] + ' template id: %s' % id_to_check
        LOG.error('%s status code: %s' % (msg, 3))
        return get_fault_result(RESULT_DESCRIPTION, 3, msg)

    return get_correct_result(RESULT_DESCRIPTION)


def _validate_entity_category(entity_to_check, category):

    if TemplateFields.CATEGORY not in entity_to_check \
            or entity_to_check[TemplateFields.CATEGORY] != category:
        msg = status_msgs[132] + ' expect %s to be %s' \
                                 % (entity_to_check, category)
        LOG.error('%s status code: %s' % (msg, 132))
        return get_fault_result(RESULT_DESCRIPTION, 132, msg)

    return get_correct_result(RESULT_DESCRIPTION)
