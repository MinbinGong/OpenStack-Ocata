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
import os

from oslo_config import cfg

from vitrage.evaluator.scenario_repository import ScenarioRepository
from vitrage.evaluator.template_validation.template_syntax_validator import \
    syntax_validation
from vitrage.tests import base
from vitrage.tests.mocks import utils
from vitrage.utils import file as file_utils


class ScenarioRepositoryTest(base.BaseTest):

    HOST_HIGH_CPU = 'host_high_cpu_load_to_instance_cpu_suboptimal'
    OPTS = [
        cfg.StrOpt('templates_dir',
                   default=utils.get_resources_dir() + '/templates/general',
                   ),
    ]

    # noinspection PyPep8Naming
    @classmethod
    def setUpClass(cls):

        cls.conf = cfg.ConfigOpts()
        cls.conf.register_opts(cls.OPTS, group='evaluator')

        templates_dir_path = cls.conf.evaluator.templates_dir
        cls.template_defs = file_utils.load_yaml_files(templates_dir_path)

        cls.scenario_repository = ScenarioRepository(cls.conf)

    def test_template_loader(self):

        # Test Action
        scenario_repository = ScenarioRepository(self.conf)

        # Test assertions
        self.assertIsNotNone(scenario_repository)
        path, dirs, files = next(os.walk(self.conf.evaluator.templates_dir))
        self.assertEqual(len(files), len(scenario_repository.templates))

    def test_init_scenario_repository(self):

        # Test Setup
        valid_template_counter = 0
        for template_definition in self.template_defs:
            syntax_validation_result = syntax_validation(template_definition)
            if syntax_validation_result.is_valid_config:
                valid_template_counter += 1

        # Test assertions
        self.assertIsNotNone(self.scenario_repository)

        scenario_templates = self.scenario_repository.templates
        self.assertEqual(valid_template_counter, len(scenario_templates))

    def test_get_scenario_by_edge(self):
        pass

    def test_get_scenario_by_entity(self):
        pass

    def test_add_template(self):
        pass
