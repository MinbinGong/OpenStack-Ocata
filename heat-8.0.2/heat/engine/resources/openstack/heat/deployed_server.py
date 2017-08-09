#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_config import cfg
from oslo_log import log as logging

from heat.common.i18n import _
from heat.engine import attributes
from heat.engine import constraints
from heat.engine import properties
from heat.engine.resources import server_base

cfg.CONF.import_opt('default_software_config_transport', 'heat.common.config')
cfg.CONF.import_opt('default_user_data_format', 'heat.common.config')
cfg.CONF.import_opt('max_server_name_length', 'heat.common.config')

LOG = logging.getLogger(__name__)


class DeployedServer(server_base.BaseServer):
    """A resource for managing servers that are already deployed.

    A DeployedServer resource manages resources for servers that have been
    deployed externally from OpenStack. These servers can be associated with
    SoftwareDeployments for further orchestration via Heat.
    """

    PROPERTIES = (
        NAME, METADATA, SOFTWARE_CONFIG_TRANSPORT
    ) = (
        'name', 'metadata', 'software_config_transport'
    )

    _SOFTWARE_CONFIG_TRANSPORTS = (
        POLL_SERVER_CFN, POLL_SERVER_HEAT, POLL_TEMP_URL, ZAQAR_MESSAGE
    ) = (
        'POLL_SERVER_CFN', 'POLL_SERVER_HEAT', 'POLL_TEMP_URL', 'ZAQAR_MESSAGE'
    )

    properties_schema = {
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Server name.'),
            update_allowed=True
        ),
        METADATA: properties.Schema(
            properties.Schema.MAP,
            _('Arbitrary key/value metadata to store for this server. Both '
              'keys and values must be 255 characters or less. Non-string '
              'values will be serialized to JSON (and the serialized '
              'string must be 255 characters or less).'),
            update_allowed=True
        ),
        SOFTWARE_CONFIG_TRANSPORT: properties.Schema(
            properties.Schema.STRING,
            _('How the server should receive the metadata required for '
              'software configuration. POLL_SERVER_CFN will allow calls to '
              'the cfn API action DescribeStackResource authenticated with '
              'the provided keypair. POLL_SERVER_HEAT will allow calls to '
              'the Heat API resource-show using the provided keystone '
              'credentials. POLL_TEMP_URL will create and populate a '
              'Swift TempURL with metadata for polling. ZAQAR_MESSAGE will '
              'create a dedicated zaqar queue and post the metadata '
              'for polling.'),
            default=cfg.CONF.default_software_config_transport,
            update_allowed=True,
            constraints=[
                constraints.AllowedValues(_SOFTWARE_CONFIG_TRANSPORTS),
            ]
        ),
    }

    ATTRIBUTES = (
        NAME_ATTR
    ) = (
        'name'
    )

    attributes_schema = {
        NAME_ATTR: attributes.Schema(
            _('Name of the server.'),
            type=attributes.Schema.STRING
        )
    }

    def __init__(self, name, json_snippet, stack):
        super(DeployedServer, self).__init__(name, json_snippet, stack)
        self._register_access_key()

    def handle_create(self):
        metadata = self.metadata_get(True) or {}
        self.resource_id_set(self.uuid)

        self._create_transport_credentials(self.properties)
        self._populate_deployments_metadata(metadata, self.properties)

        return self.resource_id

    def _delete(self):
        self._delete_queue()
        self._delete_user()
        self._delete_temp_url()


def resource_mapping():
    return {
        'OS::Heat::DeployedServer': DeployedServer,
    }
