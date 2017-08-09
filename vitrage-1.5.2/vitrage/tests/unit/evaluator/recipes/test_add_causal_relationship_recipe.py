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

from vitrage.common.constants import EdgeLabel
from vitrage.common.constants import EdgeProperties
from vitrage.evaluator.actions.base import ActionType
from vitrage.evaluator.actions.recipes.action_steps import ADD_EDGE
from vitrage.evaluator.actions.recipes.action_steps import REMOVE_EDGE
from vitrage.evaluator.actions.recipes.add_causal_relationship import \
    AddCausalRelationship
from vitrage.evaluator.template_data import ActionSpecs
from vitrage.evaluator.template_fields import TemplateFields as TField
from vitrage.graph import Vertex
from vitrage.tests import base


class AddCausalRelationshipTest(base.BaseTest):

    # noinspection PyPep8Naming
    @classmethod
    def setUpClass(cls):

        cls.target_vertex = Vertex('RESOURCE:nova.host:test_target')
        cls.source_vertex = Vertex('RESOURCE:nova.host:test_source')

        targets = {
            TField.TARGET: cls.target_vertex,
            TField.SOURCE: cls.source_vertex
        }

        cls.action_spec = ActionSpecs(ActionType.ADD_CAUSAL_RELATIONSHIP,
                                      targets,
                                      {})

    def test_get_do_recipe(self):

        # Test Action
        action_steps = AddCausalRelationship.get_do_recipe(self.action_spec)

        # Test Assertions

        # expecting for one step: add edge
        self.assertEqual(1, len(action_steps))

        self.assertEqual(ADD_EDGE, action_steps[0].type)
        add_edge_step_params = action_steps[0].params
        self.assertEqual(3, len(add_edge_step_params))

        source = add_edge_step_params.get(TField.SOURCE)
        self.assertEqual(self.source_vertex.vertex_id, source)

        target = add_edge_step_params.get(TField.TARGET)
        self.assertEqual(self.target_vertex.vertex_id, target)

        relation_name = add_edge_step_params[EdgeProperties.RELATIONSHIP_TYPE]
        self.assertEqual(EdgeLabel.CAUSES, relation_name)

    def test_get_undo_recipe(self):

        # Test Action
        action_steps = AddCausalRelationship.get_undo_recipe(self.action_spec)

        # Test Assertions

        # expecting for one step: remove edge
        self.assertEqual(1, len(action_steps))

        self.assertEqual(REMOVE_EDGE, action_steps[0].type)
        add_edge_step_params = action_steps[0].params
        self.assertEqual(3, len(add_edge_step_params))

        source = add_edge_step_params.get(TField.SOURCE)
        self.assertEqual(self.source_vertex.vertex_id, source)

        target = add_edge_step_params.get(TField.TARGET)
        self.assertEqual(self.target_vertex.vertex_id, target)

        relation_name = add_edge_step_params[EdgeProperties.RELATIONSHIP_TYPE]
        self.assertEqual(EdgeLabel.CAUSES, relation_name)
