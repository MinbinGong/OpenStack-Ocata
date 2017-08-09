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
import re
import six

from oslo_log import log
from voluptuous import All
from voluptuous import Any
from voluptuous import Error
from voluptuous import Invalid
from voluptuous import Required
from voluptuous import Schema

from vitrage.common.constants import EdgeLabel
from vitrage.common.constants import EntityCategory
from vitrage.evaluator.actions.base import action_types
from vitrage.evaluator.template_fields import TemplateFields
from vitrage.evaluator.template_validation.base import get_correct_result
from vitrage.evaluator.template_validation.base import get_fault_result
from vitrage.evaluator.template_validation.status_messages import status_msgs

LOG = log.getLogger(__name__)


RESULT_DESCRIPTION = 'Template syntax validation'


def syntax_validation(template_conf):

    result = validate_template_sections(template_conf)

    if result.is_valid_config:
        metadata = template_conf[TemplateFields.METADATA]
        result = validate_metadata_section(metadata)

    if result.is_valid_config:
        definitions = template_conf[TemplateFields.DEFINITIONS]
        result = validate_definitions_section(definitions)

    if result.is_valid_config:
        scenarios = template_conf[TemplateFields.SCENARIOS]
        result = validate_scenarios_section(scenarios)

    return result


def validate_template_sections(template_conf):

    schema = Schema({
        Required(TemplateFields.DEFINITIONS, msg=21): dict,
        Required(TemplateFields.METADATA, msg=62): dict,
        Required(TemplateFields.SCENARIOS, msg=80): list
    })
    return _validate_dict_schema(schema, template_conf)


def validate_metadata_section(metadata):

    any_str = Any(str, six.text_type)

    schema = Schema({
        Required(TemplateFields.NAME, msg=60): any_str,
        TemplateFields.DESCRIPTION: any_str
    })
    return _validate_dict_schema(schema, metadata)


def validate_definitions_section(definitions):

    if TemplateFields.RELATIONSHIPS not in definitions or \
        definitions[TemplateFields.RELATIONSHIPS] != '':
        schema = Schema({
            Required(TemplateFields.ENTITIES, msg=20): list,
            TemplateFields.RELATIONSHIPS: list
        })
        result = _validate_dict_schema(schema, definitions)

    else:
        result = get_correct_result(RESULT_DESCRIPTION)

    if result.is_valid_config:
        result = validate_entities(definitions[TemplateFields.ENTITIES])

        relationships = definitions.get(TemplateFields.RELATIONSHIPS, None)
        if result.is_valid_config and relationships:
            return validate_relationships(relationships)

    return result


def validate_entities(entities):

    if not entities:
        LOG.error('%s status code: %s' % (status_msgs[43], 43))
        return get_fault_result(RESULT_DESCRIPTION, 43)

    for entity in entities:

        schema = Schema({
            Required(TemplateFields.ENTITY, msg=46): dict,
        })
        result = _validate_dict_schema(schema, entity)

        if result.is_valid_config:
            result = validate_entity_dict(entity[TemplateFields.ENTITY])

        if not result.is_valid_config:
            return result

    return result


def validate_entity_dict(entity_dict):

    any_str = Any(str, six.text_type)
    schema = Schema({
        Required(TemplateFields.CATEGORY, msg=42):
            All(_validate_category_field()),
        TemplateFields.TYPE: any_str,
        Required(TemplateFields.TEMPLATE_ID, msg=41):
            All(_validate_template_id_value())
    }, extra=True)

    return _validate_dict_schema(schema, entity_dict)


def validate_relationships(relationships):

    for relationship in relationships:

        schema = Schema({
            Required(TemplateFields.RELATIONSHIP, msg=101): dict,
        })
        result = _validate_dict_schema(schema, relationship)

        if result.is_valid_config:
            relationship_dict = relationship[TemplateFields.RELATIONSHIP]
            result = validate_relationship_dict(relationship_dict)

            if not result.is_valid_config:
                return result
    return result


def validate_relationship_dict(relationship_dict):

    any_str = Any(str, six.text_type)
    schema = Schema({
        Required(TemplateFields.SOURCE, msg=102): any_str,
        Required(TemplateFields.TARGET, msg=103): any_str,
        TemplateFields.RELATIONSHIP_TYPE: _validate_relationship_type_field(),
        Required(TemplateFields.TEMPLATE_ID, msg=104):
            All(_validate_template_id_value())
    })
    return _validate_dict_schema(schema, relationship_dict)


def validate_scenarios_section(scenarios):

    if not scenarios:
        LOG.error('%s status code: %s' % (status_msgs[81], 81))
        return get_fault_result(RESULT_DESCRIPTION, 81)

    for scenario in scenarios:

        schema = Schema({
            Required(TemplateFields.SCENARIO, msg=82): dict,
        })
        result = _validate_dict_schema(schema, scenario)

        if result.is_valid_config:
            result = validate_scenario(scenario[TemplateFields.SCENARIO])

            if not result.is_valid_config:
                return result

    return result


def validate_scenario(scenario):

    any_str = Any(str, six.text_type)
    schema = Schema({
        Required(TemplateFields.CONDITION, msg=83): any_str,
        Required(TemplateFields.ACTIONS, msg=84): list
    })
    result = _validate_dict_schema(schema, scenario)

    if result.is_valid_config:
        return validate_actions_schema(scenario[TemplateFields.ACTIONS])

    return result


def validate_actions_schema(actions):

    if not actions:
        LOG.error('%s status code: %s' % (status_msgs[121], 121))
        return get_fault_result(RESULT_DESCRIPTION, 121)

    for action in actions:

        schema = Schema({
            Required(TemplateFields.ACTION, msg=122): dict,
        })
        result = _validate_dict_schema(schema, action)

        if result.is_valid_config:
            result = validate_action_schema(action[TemplateFields.ACTION])

        if not result.is_valid_config:
            return result

    return result


def validate_action_schema(action):

    schema = Schema({
        Required(TemplateFields.ACTION_TYPE, msg=123):
            _validate_action_type_field(),
        TemplateFields.PROPERTIES: dict,
        Required(TemplateFields.ACTION_TARGET, msg=124): dict
    })
    return _validate_dict_schema(schema, action)


def _validate_dict_schema(schema, value):

    try:
        schema(value)
    except Error as e:

        status_code = _get_status_code(e)
        if status_code:
            msg = status_msgs[status_code]
        else:
            # General syntax error
            status_code = 4
            msg = status_msgs[4] + str(e)

        LOG.error('%s status code: %s' % (msg, status_code))
        return get_fault_result(RESULT_DESCRIPTION, status_code, msg)

    return get_correct_result(RESULT_DESCRIPTION)


def _get_status_code(e):
    prefix = str(e).split(' ')[0].strip()
    if prefix.isdigit():
        return int(prefix)
    return None


def _validate_template_id_value(msg=None):
    def f(v):
        if re.match("_*[a-zA-Z]+\\w*", str(v)):
            return str(v)
        else:
            raise Invalid(msg or 1)
    return f


def _validate_category_field(msg=None):
    def f(v):
        if str(v) in EntityCategory.categories():
            return str(v)
        else:
            raise Invalid(msg or 45)
    return f


def _validate_relationship_type_field(msg=None):
    def f(v):
        if str(v) in EdgeLabel.labels():
            return str(v)
        else:
            raise Invalid(msg or 100)
    return f


def _validate_action_type_field(msg=None):
    def f(v):
        if str(v) in action_types:
            return str(v)
        else:
            raise Invalid(msg or 120)
    return f
