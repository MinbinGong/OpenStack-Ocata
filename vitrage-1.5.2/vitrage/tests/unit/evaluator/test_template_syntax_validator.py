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
import copy
import logging

from vitrage.evaluator.template_fields import TemplateFields
from vitrage.evaluator.template_validation.status_messages import status_msgs
from vitrage.evaluator.template_validation import template_syntax_validator
from vitrage.tests import base
from vitrage.tests.mocks import utils
from vitrage.utils import file as file_utils


# noinspection PyAttributeOutsideInit
class TemplateSyntaxValidatorTest(base.BaseTest):

    # noinspection PyPep8Naming
    @classmethod
    def setUpClass(cls):

        template_dir_path = '%s/templates/general' % utils.get_resources_dir()
        cls.template_yamls = file_utils.load_yaml_files(template_dir_path)
        cls.first_template = cls.template_yamls[0]

        cls._hide_useless_logging_messages()

    @property
    def clone_template(self):
        return copy.deepcopy(self.first_template)

    def test_template_validator(self):
        for template in self.template_yamls:
            self._test_execution_with_correct_result(template)

    def test_validate_template_without_metadata_section(self):

        template = self.clone_template
        template.pop(TemplateFields.METADATA)
        self._test_execution_with_fault_result(template, 62)

    def test_validate_template_without_id_in_metadata_section(self):

        template = self.clone_template
        template[TemplateFields.METADATA].pop(TemplateFields.NAME)
        self._test_execution_with_fault_result(template, 60)

    def test_validate_template_without_definitions_section(self):

        template = self.clone_template
        template.pop(TemplateFields.DEFINITIONS)
        self._test_execution_with_fault_result(template, 21)

    def test_validate_template_without_entities(self):

        template = self.clone_template
        template[TemplateFields.DEFINITIONS].pop(TemplateFields.ENTITIES)
        self._test_execution_with_fault_result(template, 20)

    def test_validate_template_with_empty_entities(self):

        template = self.clone_template
        template[TemplateFields.DEFINITIONS][TemplateFields.ENTITIES] = []
        self._test_execution_with_fault_result(template, 43)

    def test_validate_entity_without_required_fields(self):

        self._validate_entity_without_required_field(
            TemplateFields.CATEGORY, 42)

        self._validate_entity_without_required_field(
            TemplateFields.TEMPLATE_ID, 41)

    def _validate_entity_without_required_field(self,
                                                field_name,
                                                expected_comment):
        template = self.clone_template
        definitions = template[TemplateFields.DEFINITIONS]
        entity = definitions[TemplateFields.ENTITIES][0]
        entity[TemplateFields.ENTITY].pop(field_name)

        self._test_execution_with_fault_result(template, expected_comment)

    def test_validate_entity_with_invalid_template_id(self):
        template = self.clone_template
        definitions = template[TemplateFields.DEFINITIONS]
        entity = definitions[TemplateFields.ENTITIES][0]

        # template_id as integer
        entity[TemplateFields.ENTITY][TemplateFields.TEMPLATE_ID] = 1
        self._test_execution_with_fault_result(template, 1)

        # template_id as string with numbers
        entity[TemplateFields.ENTITY][TemplateFields.TEMPLATE_ID] = '123'
        self._test_execution_with_fault_result(template, 1)

        # template_id as string with numbers
        entity[TemplateFields.ENTITY][TemplateFields.TEMPLATE_ID] = '_'
        self._test_execution_with_fault_result(template, 1)

    def test_validate_correct_template_id_value(self):

        template = self.clone_template
        definitions = template[TemplateFields.DEFINITIONS]
        entity = definitions[TemplateFields.ENTITIES][0]

        entity[TemplateFields.ENTITY][TemplateFields.TEMPLATE_ID] = 'a_a'
        self._test_execution_with_correct_result(template)

        entity[TemplateFields.ENTITY][TemplateFields.TEMPLATE_ID] = 'a'
        self._test_execution_with_correct_result(template)

        entity[TemplateFields.ENTITY][TemplateFields.TEMPLATE_ID] = '_aaa'
        self._test_execution_with_correct_result(template)

        entity[TemplateFields.ENTITY][TemplateFields.TEMPLATE_ID] = '_a123'
        self._test_execution_with_correct_result(template)

    def test_validate_entity_with_invalid_category_value(self):

        template = self.clone_template
        definitions = template[TemplateFields.DEFINITIONS]
        entity = definitions[TemplateFields.ENTITIES][0]
        entity[TemplateFields.ENTITY][TemplateFields.CATEGORY] = 'unknown'

        self._test_execution_with_fault_result(template, 45)

    def test_validate_relationships_without_required_fields(self):

        self._validate_relationships_with_missing_required_field(
            TemplateFields.SOURCE, 102)

        self._validate_relationships_with_missing_required_field(
            TemplateFields.TARGET, 103)

        self._validate_relationships_with_missing_required_field(
            TemplateFields.TEMPLATE_ID, 104)

    def _validate_relationships_with_missing_required_field(self,
                                                            field_name,
                                                            expected_comment):
        template = self.clone_template
        definitions = template[TemplateFields.DEFINITIONS]
        relationship = definitions[TemplateFields.RELATIONSHIPS][0]
        relationship[TemplateFields.RELATIONSHIP].pop(field_name)

        self._test_execution_with_fault_result(template, expected_comment)

    def test_validate_relationship_with_invalid_relationship_type_field(self):

        template = self.clone_template
        definitions = template[TemplateFields.DEFINITIONS]
        relationship = definitions[TemplateFields.RELATIONSHIPS][0]
        relationship_dict = relationship[TemplateFields.RELATIONSHIP]
        relationship_dict[TemplateFields.RELATIONSHIP_TYPE] = 'unknown'

        self._test_execution_with_fault_result(template, 100)

    def test_validate_template_without_scenarios_section(self):

        template = self.clone_template
        template.pop(TemplateFields.SCENARIOS)
        self._test_execution_with_fault_result(template, 80)

    def test_validate_template_with_empty_scenarios(self):

        template = self.clone_template
        template[TemplateFields.SCENARIOS] = []
        self._test_execution_with_fault_result(template, 81)

    def test_validate_scenario_without_required_condition_field(self):

        template = self.clone_template
        scenario = template[TemplateFields.SCENARIOS][0]
        scenario[TemplateFields.SCENARIO].pop(TemplateFields.CONDITION)
        self._test_execution_with_fault_result(template, 83)

    def test_validate_scenario_without_required_actions_field(self):

        template = self.clone_template
        scenario = template[TemplateFields.SCENARIOS][0]
        scenario[TemplateFields.SCENARIO].pop(TemplateFields.ACTIONS)
        self._test_execution_with_fault_result(template, 84)

    def test_validate_template_with_no_actions(self):

        template = self.clone_template
        scenario = template[TemplateFields.SCENARIOS][0]
        scenario[TemplateFields.SCENARIO][TemplateFields.ACTIONS] = []
        self._test_execution_with_fault_result(template, 121)

    def _test_validate_action_without_required_fields(self):

        self._test_validate_action_without_required_field(
            TemplateFields.ACTION_TYPE,
            status_msgs[123])

        self._test_validate_action_without_required_field(
            TemplateFields.ACTION_TARGET,
            status_msgs[124])

    def _test_validate_action_without_required_field(self,
                                                     field_name,
                                                     expected_comment):
        template = self.clone_template
        scenario = template[TemplateFields.SCENARIOS][0]
        action = scenario[TemplateFields.SCENARIO][TemplateFields.ACTIONS][0]
        action[TemplateFields.ACTION].pop(field_name)
        self._test_execution_with_fault_result(template, expected_comment)

    def _test_validate_action_with_invalid_datasource_action(self):

        template = self.clone_template
        scenario = template[TemplateFields.SCENARIOS][0]
        action = scenario[TemplateFields.SCENARIO][TemplateFields.ACTIONS][0]
        action_dict = action[TemplateFields.ACTION]
        action_dict[TemplateFields.ACTION_TYPE] = 'unknown'

        self._test_execution_with_fault_result(template, status_msgs[100])

    def _test_execution_with_fault_result(self, template, expected_code):

        # Test action
        result = template_syntax_validator.syntax_validation(template)

        # Test assertions
        self.assertFalse(result.is_valid_config)
        self.assertTrue(result.comment.startswith(status_msgs[expected_code]))
        self.assertEqual(result.status_code, expected_code)

    def _test_execution_with_correct_result(self, template):

        # Test action
        result = template_syntax_validator.syntax_validation(template)

        # Test assertions
        self.assertTrue(result.is_valid_config)
        self.assertEqual(result.comment, status_msgs[0])
        self.assertEqual(result.status_code, 0)

    @staticmethod
    def _hide_useless_logging_messages():

        validator_path = 'vitrage.evaluator.template_validation.' \
                         'template_syntax_validator'
        syntax_validator_log = logging.getLogger(validator_path)
        syntax_validator_log.setLevel(logging.FATAL)
