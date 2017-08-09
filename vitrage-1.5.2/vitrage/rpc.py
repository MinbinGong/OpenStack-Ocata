# Copyright 2015 - Alcatel-Lucent
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


from oslo_config import cfg
import oslo_messaging as messaging

OPTS = [
    cfg.StrOpt('rpc_topic',
               default='rpcapiv1',
               help='The topic vitrage listens on'),
]


def set_defaults(control_exchange):
    messaging.set_transport_defaults(control_exchange)


def get_client(transport, target, version_cap=None, serializer=None):
    assert transport is not None
    return messaging.RPCClient(transport,
                               target,
                               version_cap=version_cap,
                               serializer=serializer)


def get_server(target, endpoints, transport, serializer=None):
    assert transport is not None
    return messaging.get_rpc_server(transport,
                                    target,
                                    endpoints,
                                    executor='eventlet',
                                    serializer=serializer)
