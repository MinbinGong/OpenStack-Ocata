# Copyright 2016 - Nokia, ZTE
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR  CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo_config import cfg
from vitrage.common.constants import TopologyFields
from vitrage.common.constants import UpdateMethod

STATIC_DATASOURCE = 'static'

OPTS = [
    cfg.StrOpt('transformer',
               default='vitrage.datasources.static.transformer.'
                       'StaticTransformer',
               help='Static transformer class path',
               required=True),
    cfg.StrOpt('driver',
               default='vitrage.datasources.static.driver.'
                       'StaticDriver',
               help='Static driver class path',
               required=True),
    cfg.StrOpt('update_method',
               default=UpdateMethod.PULL,
               help='None: updates only via Vitrage periodic snapshots.'
                    'Pull: updates periodically.'
                    'Push: updates by getting notifications from the'
                    ' datasource itself.',
               required=True),
    cfg.IntOpt('changes_interval',
               default=30,
               help='interval in seconds between checking changes in the'
                    'static configuration files'),
    # NOTE: This folder is already used by static_physical datasource. Legacy
    # configuration files will NOT be converted automatically. But user will
    # receive deprecation warnings.
    cfg.StrOpt('directory', default='/etc/vitrage/static_datasources',
               help='static data sources configuration directory')]


class StaticFields(TopologyFields):
    STATIC_ID = 'static_id'
