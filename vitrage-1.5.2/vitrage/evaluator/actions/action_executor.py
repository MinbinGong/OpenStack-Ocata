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

from oslo_utils import importutils

from vitrage.common.constants import DatasourceAction as AType
from vitrage.common.constants import DatasourceProperties as DSProps
from vitrage.common.constants import VertexProperties as VProps
from vitrage.evaluator.actions.base import ActionMode
from vitrage.evaluator.actions.base import ActionType
from vitrage.evaluator.actions.evaluator_event_transformer import VITRAGE_TYPE
from vitrage.evaluator.actions.recipes.action_steps import ADD_EDGE
from vitrage.evaluator.actions.recipes.action_steps import ADD_VERTEX
from vitrage.evaluator.actions.recipes.action_steps import REMOVE_EDGE
from vitrage.evaluator.actions.recipes.action_steps import REMOVE_VERTEX
from vitrage.evaluator.actions.recipes.action_steps import UPDATE_VERTEX
from vitrage.evaluator.actions.recipes.add_causal_relationship import \
    AddCausalRelationship
from vitrage.evaluator.actions.recipes.base import EVALUATOR_EVENT_TYPE
from vitrage.evaluator.actions.recipes.mark_down import MarkDown
from vitrage.evaluator.actions.recipes.raise_alarm import RaiseAlarm
from vitrage.evaluator.actions.recipes.set_state import SetState
from vitrage.utils import datetime as datetime_utils


class ActionExecutor(object):

    def __init__(self, event_queue):
        self.event_queue = event_queue
        self.action_recipes = ActionExecutor._register_action_recipes()

        self.action_step_defs = {
            ADD_VERTEX: self.add_vertex,
            REMOVE_VERTEX: self.remove_vertex,
            UPDATE_VERTEX: self.update_vertex,
            ADD_EDGE: self.add_edge,
            REMOVE_EDGE: self.remove_edge,
        }

    def execute(self, action_spec, action_mode):

        action_recipe = self.action_recipes[action_spec.type]
        if action_mode == ActionMode.DO:
            steps = action_recipe.get_do_recipe(action_spec)
        else:
            steps = action_recipe.get_undo_recipe(action_spec)

        for step in steps:
            self.action_step_defs[step.type](step.params)

    def add_vertex(self, params):

        event = copy.deepcopy(params)
        ActionExecutor._add_default_properties(event)
        event[EVALUATOR_EVENT_TYPE] = ADD_VERTEX

        self.event_queue.put(event)

    def update_vertex(self, params):

        event = copy.deepcopy(params)
        ActionExecutor._add_default_properties(event)
        event[EVALUATOR_EVENT_TYPE] = UPDATE_VERTEX

        self.event_queue.put(event)

    def remove_vertex(self, params):
        event = copy.deepcopy(params)
        ActionExecutor._add_default_properties(event)
        event[EVALUATOR_EVENT_TYPE] = REMOVE_VERTEX

        self.event_queue.put(event)

    def add_edge(self, params):

        event = copy.deepcopy(params)
        ActionExecutor._add_default_properties(event)
        event[EVALUATOR_EVENT_TYPE] = ADD_EDGE

        self.event_queue.put(event)

    def remove_edge(self, params):

        event = copy.deepcopy(params)
        ActionExecutor._add_default_properties(event)
        event[EVALUATOR_EVENT_TYPE] = REMOVE_EDGE

        self.event_queue.put(event)

    @staticmethod
    def _add_default_properties(event):

        event[DSProps.DATASOURCE_ACTION] = AType.UPDATE
        event[DSProps.ENTITY_TYPE] = VITRAGE_TYPE
        event[VProps.UPDATE_TIMESTAMP] = str(datetime_utils.utcnow(False))
        event[VProps.SAMPLE_TIMESTAMP] = str(datetime_utils.utcnow())

    @staticmethod
    def _register_action_recipes():

        # noinspection PyDictCreation
        recipes = {}

        recipes[ActionType.SET_STATE] = importutils.import_object(
            "%s.%s" % (SetState.__module__, SetState.__name__))

        recipes[ActionType.RAISE_ALARM] = importutils.import_object(
            "%s.%s" % (RaiseAlarm.__module__, RaiseAlarm.__name__))

        recipes[ActionType.ADD_CAUSAL_RELATIONSHIP] = \
            importutils.import_object(
            "%s.%s" % (AddCausalRelationship.__module__,
                       AddCausalRelationship.__name__))

        recipes[ActionType.MARK_DOWN] = importutils.import_object(
            "%s.%s" % (MarkDown.__module__, MarkDown.__name__))

        return recipes
