# Copyright 2016 - Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo_service import service as os_service
import sys

from vitrage.notifier.service import VitrageNotifierService
from vitrage import service


def main():
    conf = service.prepare_service()
    launcher = os_service.ServiceLauncher(conf)
    launcher.launch_service(VitrageNotifierService(conf))
    launcher.wait()


if __name__ == "__main__":
    sys.exit(main())
