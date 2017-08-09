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


class InitializationStatus(object):
    STARTED = 'started'
    RECEIVED_ALL_END_MESSAGES = 'received_all_end_messages'
    FINISHED = 'finished'

    def __init__(self):
        self.status = self.STARTED
        self.end_messages = {}

    def is_initialization_finished(self):
        return self.status == self.FINISHED

    def is_received_all_end_messages(self):
        return self.status == self.RECEIVED_ALL_END_MESSAGES
