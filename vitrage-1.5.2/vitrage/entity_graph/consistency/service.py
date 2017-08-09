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

from oslo_log import log
from oslo_service import service as os_service
import threading

from vitrage.entity_graph.consistency.consistency_enforcer \
    import ConsistencyEnforcer

LOG = log.getLogger(__name__)


class VitrageGraphConsistencyService(os_service.Service):

    def __init__(self,
                 conf,
                 evaluator_queue,
                 evaluator,
                 entity_graph,
                 initialization_status):
        super(VitrageGraphConsistencyService, self).__init__()
        self.conf = conf
        self.evaluator_queue = evaluator_queue
        self.evaluator = evaluator
        self.entity_graph = entity_graph
        self.initialization_status = initialization_status

    def start(self):
        LOG.info("Vitrage Graph Consistency Service - Starting...")

        super(VitrageGraphConsistencyService, self).start()

        consistency_enf = ConsistencyEnforcer(self.conf,
                                              self.evaluator_queue,
                                              self.evaluator,
                                              self.entity_graph,
                                              self.initialization_status)
        self.tg.add_timer(self.conf.datasources.snapshots_interval,
                          consistency_enf.periodic_process,
                          initial_delay=60 +
                          self.conf.datasources.snapshots_interval)

        initializing_process_thread = \
            threading.Thread(target=consistency_enf.initializing_process)
        initializing_process_thread.start()

        LOG.info("Vitrage Graph Consistency Service - Started!")

    def stop(self, graceful=False):
        LOG.info("Vitrage Graph Consistency Service - Stopping...")

        super(VitrageGraphConsistencyService, self).stop()

        LOG.info("Vitrage Graph Consistency Service - Stopped!")
