# Copyright 2015 - Alcatel-Lucent
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

import datetime

from oslo_log import log
from oslo_service import service as os_service

from vitrage.entity_graph.processor import processor as proc

LOG = log.getLogger(__name__)


class VitrageGraphService(os_service.Service):

    def __init__(self,
                 conf,
                 event_queue,
                 evaluator_queue,
                 evaluator,
                 entity_graph,
                 initialization_status):
        super(VitrageGraphService, self).__init__()
        self.queue = event_queue
        self.conf = conf
        self.evaluator = evaluator
        self.processor = proc.Processor(self.conf,
                                        initialization_status,
                                        e_graph=entity_graph)
        self.evaluator_queue = evaluator_queue

    def start(self):
        LOG.info("Vitrage Graph Service - Starting...")

        super(VitrageGraphService, self).start()
        self.tg.add_timer(0.1, self._process_event_non_blocking)

        LOG.info("Vitrage Graph Service - Started!")

    def stop(self, graceful=False):
        LOG.info("Vitrage Graph Service - Stopping...")

        super(VitrageGraphService, self).stop(graceful)

        LOG.info("Vitrage Graph Service - Stopped!")

    def _process_events(self):
        while True:
            self._process_event_non_blocking()

    def _process_event_non_blocking(self):
        """Process events received from datasource

        In order that other services (such as graph consistency, api handler)
        could get work time as well, the work processing performed for 2
        seconds and goes to sleep for 1 second. if there are more events in
        the queue they are done when timer returns.
        """
        start_time = datetime.datetime.now()
        while not self.evaluator_queue.empty() or not self.queue.empty():
            time_delta = datetime.datetime.now() - start_time
            if time_delta.total_seconds() >= 2:
                break
            if not self.evaluator_queue.empty():
                self.do_process(self.evaluator_queue)
            elif not self.queue.empty():
                self.do_process(self.queue)

    def do_process(self, queue):
        try:
            event = queue.get()
            self.processor.process_event(event)
        except Exception as e:
            LOG.exception("Exception: %s", e)
