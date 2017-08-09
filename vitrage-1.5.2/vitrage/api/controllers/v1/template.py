# Copyright 2016 - Nokia Corporation
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
import pecan

from oslo_log import log
from pecan.core import abort

from vitrage.api.controllers.rest import RootRestController
from vitrage.api.policy import enforce
from vitrage.i18n import _LI


LOG = log.getLogger(__name__)


class TemplateController(RootRestController):

    @pecan.expose('json')
    def get_all(self):

        LOG.info(_LI('returns template list'))

        enforce("template list",
                pecan.request.headers,
                pecan.request.enforcer,
                {})
        try:
            return self._get_templates()
        except Exception as e:
            LOG.exception('failed to get template list %s', e)
            abort(404, str(e))

    @pecan.expose('json')
    def get(self, template_uuid):

        LOG.info(_LI('get template content'))

        enforce("template show",
                pecan.request.headers,
                pecan.request.enforcer,
                {})

        try:
            return self._show_template(template_uuid)
        except Exception as e:
            LOG.exception('failed to show template %s' % template_uuid, e)
            abort(404, str(e))

    @pecan.expose('json')
    def post(self, **kwargs):

        LOG.info(_LI('validate template. args: %s') % kwargs)

        enforce("template validate",
                pecan.request.headers,
                pecan.request.enforcer,
                {})

        templates = kwargs['templates']

        try:
            return self._validate(templates)
        except Exception as e:
            LOG.exception('failed to validate template(s) %s', e)
            abort(404, str(e))

    @staticmethod
    def _get_templates():
        templates_json = pecan.request.client.call(pecan.request.context,
                                                   'get_templates')
        LOG.info(templates_json)

        try:
            template_list = json.loads(templates_json)['templates_details']
            return template_list
        except Exception as e:
            LOG.exception('failed to get template list %s ', e)
            abort(404, str(e))

    @staticmethod
    def _show_template(template_uuid):

        template_json = pecan.request.client.call(pecan.request.context,
                                                  'show_template',
                                                  template_uuid=template_uuid)
        LOG.info(template_json)

        try:
            return json.loads(template_json)
        except Exception as e:
            LOG.exception('failed to show template with uuid: %s ', e)
            abort(404, str(e))

    @staticmethod
    def _validate(templates):

        result_json = pecan.request.client.call(pecan.request.context,
                                                'validate_template',
                                                templates=templates)
        try:
            return json.loads(result_json)
        except Exception as e:
            LOG.exception('failed to open template file(s) %s ', e)
            abort(404, str(e))
