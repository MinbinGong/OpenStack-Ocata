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
from collections import namedtuple
from sympy.logic.boolalg import And
from sympy.logic.boolalg import Not
from sympy.logic.boolalg import Or
from sympy.logic.boolalg import to_dnf as sympy_to_dfn
from sympy import Symbol


from vitrage.evaluator.template_fields import TemplateFields as TFields
from vitrage.graph import Edge
from vitrage.graph import Vertex


ConditionVar = namedtuple('ConditionVar', ['variable', 'type', 'positive'])
ActionSpecs = namedtuple('ActionSpecs', ['type', 'targets', 'properties'])
Scenario = namedtuple('Scenario', ['id', 'condition', 'actions'])
EdgeDescription = namedtuple('EdgeDescription', ['edge', 'source', 'target'])


ENTITY = 'entity'
RELATIONSHIP = 'relationship'


# noinspection PyAttributeOutsideInit
class TemplateData(object):

    def __init__(self, template_def):

        self.name = template_def[TFields.METADATA][TFields.NAME]

        defs = template_def[TFields.DEFINITIONS]
        self.entities = self._build_entities(defs[TFields.ENTITIES])

        self.relationships = {}
        if TFields.RELATIONSHIPS in defs:
            self.relationships = self._build_relationships(
                defs[TFields.RELATIONSHIPS])

        self.scenarios = self._build_scenarios(template_def[TFields.SCENARIOS])

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, template_name):
        self._name = template_name

    @property
    def entities(self):
        return self._entities

    @entities.setter
    def entities(self, entities):
        self._entities = entities

    @property
    def relationships(self):
        return self._relationships

    @relationships.setter
    def relationships(self, relationships):
        self._relationships = relationships

    @property
    def scenarios(self):
        return self._scenarios

    @scenarios.setter
    def scenarios(self, scenarios):
        self._scenarios = scenarios

    def _build_entities(self, entities_defs):

        entities = {}
        for entity_def in entities_defs:

            entity_dict = entity_def[TFields.ENTITY]
            template_id = entity_dict[TFields.TEMPLATE_ID]
            properties = self._extract_properties(entity_dict)
            entities[template_id] = Vertex(template_id, properties)

        return entities

    def _build_relationships(self, relationships_defs):

        relationships = {}
        for relationship_def in relationships_defs:

            relationship_dict = relationship_def[TFields.RELATIONSHIP]
            relationship = self._extract_relationship_info(relationship_dict)
            template_id = relationship_dict[TFields.TEMPLATE_ID]
            relationships[template_id] = relationship

        return relationships

    def _extract_relationship_info(self, relationship_dict):

        source_id = relationship_dict[TFields.SOURCE]
        target_id = relationship_dict[TFields.TARGET]

        edge = Edge(source_id,
                    target_id,
                    relationship_dict[TFields.RELATIONSHIP_TYPE],
                    self._extract_properties(relationship_dict))

        source = self.entities[source_id]
        target = self.entities[target_id]
        return EdgeDescription(edge, source, target)

    @staticmethod
    def _extract_properties(var_dict):

        ignore_ids = [TFields.TEMPLATE_ID, TFields.SOURCE, TFields.TARGET]
        return dict((key, var_dict[key]) for key in var_dict
                    if key not in ignore_ids)

    def _build_scenarios(self, scenarios_defs):

        scenarios = []
        for counter, scenarios_def in enumerate(scenarios_defs):

            scenario_dict = scenarios_def[TFields.SCENARIO]
            condition = self._parse_condition(scenario_dict[TFields.CONDITION])
            action_specs = self._build_actions(scenario_dict[TFields.ACTIONS])
            scenario_id = "%s-scenario%s" % (self.name, str(counter))
            scenarios.append(Scenario(scenario_id, condition, action_specs))

        return scenarios

    @staticmethod
    def _build_actions(actions_def):

        actions = []
        for action_def in actions_def:

            action_dict = action_def[TFields.ACTION]
            action_type = action_dict[TFields.ACTION_TYPE]
            targets = action_dict[TFields.ACTION_TARGET]
            properties = action_dict.get(TFields.PROPERTIES, {})

            actions.append(ActionSpecs(action_type, targets, properties))

        return actions

    def _parse_condition(self, condition_str):
        """Parse condition string into an object

        The condition object will be converted here into DNF (Disjunctive
        Normal Form), e.g., (X and Y) or (X and Z) or (X and V and not W)...
        where X, Y, Z, V, W are either entities or relationships
        more details: https://en.wikipedia.org/wiki/Disjunctive_normal_form

        The condition object itself is a list of tuples. each tuple represents
        an AND expression compound ConditionElements. The list presents the
        OR expression e.g. [(condition_element1, condition_element2)]

        :param condition_str: the string as it written in the template itself
        :return: Condition object
        """

        condition_dnf = self.convert_to_dnf_format(condition_str)

        if isinstance(condition_dnf, Or):
            return self._extract_or_condition(condition_dnf)

        if isinstance(condition_dnf, And):
            return [self._extract_and_condition(condition_dnf)]

        if isinstance(condition_dnf, Not):
            return [[(self._extract_condition_var(condition_dnf, False))]]

        if isinstance(condition_dnf, Symbol):
            return [[(self._extract_condition_var(condition_dnf, True))]]

    @staticmethod
    def convert_to_dnf_format(condition_str):

        condition_str = condition_str.replace(' and ', '&')
        condition_str = condition_str.replace(' or ', '|')
        condition_str = condition_str.replace(' not ', '~')

        return sympy_to_dfn(condition_str)

    def _extract_or_condition(self, or_condition):

        vars_ = []
        for var in or_condition.args:

            if isinstance(var, And):
                vars_.append(self._extract_and_condition(var))
            else:
                is_symbol = isinstance(var, Symbol)
                vars_.append([self._extract_condition_var(var, is_symbol)])

        return vars_

    def _extract_and_condition(self, and_condition):
        return [self._extract_condition_var(arg, isinstance(arg, Symbol))
                for arg in and_condition.args]

    def _extract_condition_var(self, symbol, positive):

        var, var_type = self._extract_var(str(symbol))
        return ConditionVar(var, var_type, positive)

    def _extract_var(self, template_id):

        if template_id in self.relationships:
            return self.relationships[template_id], RELATIONSHIP

        return self.entities[template_id], ENTITY
