#!/usr/bin/env bash
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

#sudo chmod -R a+rw /opt/stack/
DEVSTACK_PATH="$BASE/new"
#(cd $DEVSTACK_PATH/tempest/; sudo virtualenv .venv)
#source $DEVSTACK_PATH/tempest/.venv/bin/activate

if [ "$1" = "api" ]; then
  TESTS="topology"
elif [ "$1" = "datasources" ]; then
  TESTS="datasources"
else
  TESTS="topology"
fi

#(cd $DEVSTACK_PATH/tempest/; sudo pip install -r requirements.txt -r test-requirements.txt)

(cd $DEVSTACK_PATH/; sudo sh -c 'cp -rf vitrage/vitrage_tempest_tests/tests/resources/static_physical/static_physical_configuration.yaml /etc/vitrage/')
(cd $DEVSTACK_PATH/; sudo sh -c 'cp -rf vitrage/vitrage_tempest_tests/tests/resources/templates/api/* /etc/vitrage/templates/')
(cd $DEVSTACK_PATH/; sudo sh -c 'cp -rf vitrage/vitrage_tempest_tests/tests/resources/heat/heat_template.yaml /etc/vitrage/')
(cd $DEVSTACK_PATH/; sudo sh -c 'cp -rf vitrage/vitrage_tempest_tests/tests/resources/heat/policy.json-tempest /etc/heat/')


sudo cp $DEVSTACK_PATH/tempest/etc/logging.conf.sample $DEVSTACK_PATH/tempest/etc/logging.conf

#(cd $DEVSTACK_PATH/vitrage/; sudo pip install -r requirements.txt -r  test-requirements.txt)
#(cd $DEVSTACK_PATH/vitrage/; sudo python setup.py install)


(cd $BASE/new/tempest/; sudo -E testr init)

echo "Listing existing Tempest tests"
(cd $DEVSTACK_PATH/tempest/; sudo sh -c 'testr list-tests vitrage_tempest_tests')
(cd $DEVSTACK_PATH/tempest/; sudo sh -c 'testr list-tests vitrage_tempest_tests | grep -E '$TESTS' > vitrage_tempest_tests.list')
echo "Testing $1: $TESTS..."
(cd $DEVSTACK_PATH/tempest/; sudo sh -c 'testr run --subunit --load-list=vitrage_tempest_tests.list | subunit-trace --fails')
