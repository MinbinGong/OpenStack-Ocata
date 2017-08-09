# Copyright 2016 - Alcatel-Lucent
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,  software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND,  either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from vitrage.datasources.nova.host import NOVA_HOST_DATASOURCE
from vitrage.datasources.nova.nova_driver_base import NovaDriverBase


class HostDriver(NovaDriverBase):

    @staticmethod
    def filter_none_compute_hosts(entities):
        compute_hosts = []
        for host in entities:
            host_dict = host.__dict__
            if host_dict['service'] and host_dict['service'] == 'compute':
                compute_hosts.append(host_dict)
        return compute_hosts

    def get_all(self, datasource_action):
        return self.make_pickleable(
            self.filter_none_compute_hosts(self.client.hosts.list()),
            NOVA_HOST_DATASOURCE,
            datasource_action,
            'manager')
