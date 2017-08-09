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

from datetime import datetime
from vitrage.datasources.rescheduler import ReScheduler
from vitrage.tests import base

RESCHEDULING_TIMES = 2
STANDARD_INTERVAL = 0.8
FAULT_INTERVAL = 0.2
TTL = 3
FAULT_NUM = 2
TIME_DIFF_MARGIN_PRECENT = 1.05


class ReschedulerTester(base.BaseTest):

    class DummyException(Exception):

        def __init__(self, message=''):
            self.message = message

    def rescheduled_func(self, item, assert_timing=False):
        self.counter += 1
        self.list.append(item)
        if assert_timing:
            if self.last_failure:
                current_failure = datetime.now()
                time_diff = (current_failure - self.last_failure).seconds
                self.last_failure = current_failure
                self.assertLess(time_diff,
                                STANDARD_INTERVAL * TIME_DIFF_MARGIN_PRECENT)
            else:
                self.last_failure = datetime.now()

    def rescheduled_func_with_exception(self, item):
        self.counter += 1
        self.list.append(item)
        if self.counter > RESCHEDULING_TIMES // 2 \
                and self.fault_counter < FAULT_NUM:
            raise self.DummyException('ReScheduler Test Dummy Exception')

    def rescheduled_func_callback(self, exception, item, assert_timing=False):
        self.fault_counter += 1
        self.fault_list.append(item)
        if assert_timing:
            if self.last_failure:
                current_failure = datetime.now()
                time_diff = (current_failure - self.last_failure).seconds
                self.last_failure = current_failure
                self.assertLess(time_diff,
                                FAULT_INTERVAL * TIME_DIFF_MARGIN_PRECENT)
            else:
                self.last_failure = datetime.now()

    @classmethod
    def reset_test_params(cls):
        cls.counter = 0
        cls.list = []
        cls.last_success = None
        cls.fault_counter = 0
        cls.fault_list = []
        cls.last_failure = None

    @classmethod
    def setUpClass(cls):
        cls.rescheduler = ReScheduler()
        cls.counter = 0
        cls.last_success = None
        cls.fault_counter = 0
        cls.last_failure = None
        cls.list = []
        cls.fault_list = []

    def test_schedule(self):
        # Test setup
        self.reset_test_params()
        TASKS_NUM = 6
        # Test action
        for i in range(TASKS_NUM):
            self.rescheduler.schedule(func=self.rescheduled_func, args=(i,),
                                      initial_delay=0,
                                      standard_interval=STANDARD_INTERVAL,
                                      fault_interval=FAULT_INTERVAL,
                                      times=RESCHEDULING_TIMES)
        # Test assertions
        self.assertEqual(len(self.rescheduler.scheduler.queue), TASKS_NUM)
        self.reset_test_params()

    def test_reset(self):
        # Test setup
        self.reset_test_params()
        TASKS_NUM = 6
        for i in range(TASKS_NUM):
            self.rescheduler.schedule(func=self.rescheduled_func, args=(i,),
                                      initial_delay=0,
                                      standard_interval=STANDARD_INTERVAL,
                                      fault_interval=FAULT_INTERVAL,
                                      times=RESCHEDULING_TIMES)
        # Test action
        self.rescheduler.reset()
        # Test assertions
        self.assertEqual(len(self.rescheduler.scheduler.queue), 0)
        self.reset_test_params()

    def test_rescheduling(self):
        # Test setup
        self.reset_test_params()
        TASKS_NUM = 2
        VALIDATE_LIST = [0, 1] * RESCHEDULING_TIMES
        for i in range(TASKS_NUM):
            self.rescheduler.schedule(func=self.rescheduled_func, args=(i,),
                                      initial_delay=0,
                                      standard_interval=STANDARD_INTERVAL,
                                      fault_interval=FAULT_INTERVAL,
                                      times=RESCHEDULING_TIMES)
        # Test action
        self.rescheduler.run()
        # Test assertions
        self.assertEqual(self.counter, TASKS_NUM * RESCHEDULING_TIMES)
        self.assert_list_equal(self.list, VALIDATE_LIST)
        self.reset_test_params()

    def test_rescheduling_timing(self):
        # Test setup
        self.reset_test_params()
        TASKS_NUM = 6
        for i in range(TASKS_NUM):
            self.rescheduler.schedule(
                func=self.rescheduled_func,
                args=(i, True),
                initial_delay=0,
                standard_interval=STANDARD_INTERVAL,
                fault_interval=FAULT_INTERVAL,
                times=RESCHEDULING_TIMES)
        # Test action
        # Test assertions
        self.rescheduler.run()
        self.reset_test_params()

    def test_rescheduling_with_fault_callbacks(self):
        # Test setup
        self.reset_test_params()
        VALIDATE_LIST = [0] * (RESCHEDULING_TIMES + FAULT_NUM)
        VALIDATE_FAULT_LIST = ['f'] * FAULT_NUM
        self.rescheduler.schedule(
            func=self.rescheduled_func_with_exception,
            args=(0,),
            initial_delay=0,
            standard_interval=STANDARD_INTERVAL,
            fault_interval=FAULT_INTERVAL,
            fault_callback=self.rescheduled_func_callback,
            fault_callback_kwargs={'item': 'f'},
            times=RESCHEDULING_TIMES)
        # Test action
        self.rescheduler.run()
        # Test assertions
        self.assertEqual(self.counter, RESCHEDULING_TIMES + FAULT_NUM)
        self.assert_list_equal(self.list, VALIDATE_LIST)
        self.assertEqual(self.fault_counter, FAULT_NUM)
        self.assertEqual(self.fault_list, VALIDATE_FAULT_LIST)
        self.reset_test_params()

    def test_rescheduling_with_fault_callbacks_timing(self):
        # Test setup
        self.reset_test_params()
        TASKS_NUM = 6
        for i in range(TASKS_NUM):
            self.rescheduler.schedule(
                func=self.rescheduled_func_with_exception,
                args=(i,),
                initial_delay=0,
                standard_interval=STANDARD_INTERVAL,
                fault_interval=FAULT_INTERVAL,
                fault_callback=self.rescheduled_func_callback,
                fault_callback_kwargs={'item': self.fault_counter,
                                       'assert_timing': True},
                times=RESCHEDULING_TIMES)
        # Test action
        # Test assertions
        self.rescheduler.run()
        self.reset_test_params()

    def test_rescheduling_with_ttl(self):
        # Test setup
        self.reset_test_params()
        start = datetime.now()
        self.rescheduler.schedule(
            func=self.rescheduled_func_with_exception,
            args=(0,),
            initial_delay=0,
            standard_interval=STANDARD_INTERVAL,
            fault_interval=FAULT_INTERVAL,
            fault_callback=self.rescheduled_func_callback,
            fault_callback_kwargs={'item': self.fault_counter},
            ttl=TTL)
        # Test action
        self.rescheduler.run()
        # Test assertions
        self.assertLess((datetime.now() - start).seconds,
                        TTL * TIME_DIFF_MARGIN_PRECENT)
