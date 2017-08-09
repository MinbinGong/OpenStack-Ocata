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

import json
from oslo_log import log

from vitrage.evaluator.template_fields import TemplateFields
from vitrage.evaluator.template_validation.status_messages import status_msgs
from vitrage.evaluator.template_validation.template_content_validator import \
    content_validation
from vitrage.evaluator.template_validation.template_syntax_validator import \
    syntax_validation


LOG = log.getLogger(__name__)


class TemplateApis(object):

    FAILED_MSG = 'validation failed'
    OK_MSG = 'validation OK'

    def __init__(self, templates):
        self.templates = templates

    def get_templates(self, ctx):
        LOG.debug("TemplateApis get_templates")

        templates_details = []
        for uuid, template in self.templates.items():

            template_metadata = template.data[TemplateFields.METADATA]

            templates_details.append({
                'uuid': str(template.uuid),
                'name': template_metadata[TemplateFields.NAME],
                'status': self._get_template_status(template.result),
                'status details': template.result.comment,
                'date': template.date.strftime('%Y-%m-%dT%H:%M:%SZ')
            })
        return json.dumps({'templates_details': templates_details})

    def show_template(self, ctx, template_uuid):

        LOG.debug("Show template with uuid: %s", str(template_uuid))

        template = self.templates[template_uuid]

        if template:
            return json.dumps(template.data)
        else:
            return json.dumps({'ERROR': 'Incorrect uuid'})

    def validate_template(self, ctx, templates):
        LOG.debug("TemplateApis validate_template templates:"
                  "%s", str(templates))

        results = []
        for template in templates:

            template_def = template[1]
            path = template[0]

            syntax_result = syntax_validation(template_def)
            if not syntax_result.is_valid_config:
                self._add_result(path,
                                 self.FAILED_MSG,
                                 syntax_result.description,
                                 syntax_result.comment,
                                 syntax_result.status_code,
                                 results)
                continue

            content_result = content_validation(template_def)
            if not content_result.is_valid_config:
                self._add_result(path,
                                 self.FAILED_MSG,
                                 content_result.description,
                                 content_result.comment,
                                 content_result.status_code,
                                 results)
                continue

            self._add_result(path,
                             self.OK_MSG,
                             'Template validation',
                             status_msgs[0],
                             0,
                             results)

        return json.dumps({'results': results})

    @staticmethod
    def _add_result(template_path, status, description, message, status_code,
                    results):

        results.append({
            'file path': template_path,
            'status': status,
            'description': description,
            'message': str(message),
            'status code': status_code
        })

    @staticmethod
    def _get_template_status(result):

        if result.is_valid_config:
            return 'pass'
        else:
            return 'failed'
