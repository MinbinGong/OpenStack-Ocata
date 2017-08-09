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
import sched
import time


class ReScheduler(object):

    """Rescheduler

    The ReScheduler is a decorating class to Python's sched package Scheduler.
    Allows scheduling tasks for a repeated number of times while providing
    a mechanism to reschedule differently in case of a task's failure.
    """

    def __init__(self):
        self.scheduler = sched.scheduler(time.time, time.sleep)

    def run(self):
        """Starts the scheduler

        :return: None
        """

        self.scheduler.run()

    def reset(self):
        """Removes all scheduled tasks from scheduler

        :return: None
        """

        for event in self.scheduler.queue:
            self._cancel(event=event)

    def schedule(self,
                 func,
                 args=(),
                 initial_delay=0,
                 standard_interval=None,
                 fault_interval=None,
                 standard_priority=2,
                 fault_priority=1,
                 times=-1,
                 ttl=None,
                 fault_callback=None,
                 fault_callback_kwargs={}):
        """Schedule a new task

        :param func: function to run
        :type func: function
        :param args: arguments for the function, must come as a tuple
        :type args: tuple
        :param initial_delay: initial delay before first schedule
        :type initial_delay: float
        :param standard_interval: interval between rescheduling in case of
               success
        :type standard_interval: float
        :param fault_interval: interval between rescheduling in case of failure
        :type fault_interval: float
        :param standard_priority: standard priority for scheduled task
        :type standard_priority: int
        :param fault_priority: priority for rescheduled task on failure
        :type fault_priority: int
        :param times: times to reschedule a successful task
        :type times: int
        :param fault_callback: callback function in case of failure,
               must accept 'exception' as a function keyword
        :type fault_callback: function
        :param fault_callback_kwargs: callback function in case of failure
               keyword arguments, must come as a dictionary
        :type fault_callback_kwargs: dict
        :return: None
        """

        if times == 0:
            return None

        if not func:
            raise ValueError('Invalid func value')

        if initial_delay < 0:
            raise ValueError('Initial delay is less than zero')

        if standard_interval is None and time != 1:
            raise ValueError('Standard interval is None')

        if standard_interval and standard_interval <= 0:
            raise ValueError('Standard interval is less than or equal to zero')

        if fault_interval is None:
            raise ValueError('Fault interval is None')

        if fault_interval <= 0:
            raise ValueError('Fault interval is less than or equal to zero')

        task = self._Task(
            self.scheduler,
            func,
            args,
            initial_delay,
            standard_interval,
            fault_interval,
            standard_priority,
            fault_priority,
            times,
            ttl,
            fault_callback,
            fault_callback_kwargs)

        task.reschedule()

    def _cancel(self, event):
        self.scheduler.cancel(event=event)

    class _Task(object):

        def __init__(self,
                     scheduler,
                     func,
                     args,
                     initial_delay,
                     standard_interval,
                     fault_interval,
                     standard_priority=2,
                     fault_priority=1,
                     times=-1,
                     ttl=None,
                     fault_callback=None,
                     fault_callback_kwargs={}):

            self.scheduler = scheduler
            self.func = func
            self.args = args
            self.next_schedule = initial_delay
            self.standard_interval = standard_interval
            self.fault_interval = fault_interval
            self.standard_priority = standard_priority
            self.fault_priority = fault_priority
            self.times = times
            self.fault_callback = fault_callback
            self.fault_callback_kwargs = fault_callback_kwargs
            self.ttl = ttl
            self.next_priority = self.standard_priority
            self.first_run_time = None

        @property
        def exhausted(self):
            if self.first_run_time and self.ttl:
                time_diff = (datetime.now() - self.first_run_time).seconds + \
                    self.next_schedule
                return self.ttl <= time_diff or self.times == 0

            return self.times == 0

        def run(self):
            if self.first_run_time is None:
                self.first_run_time = datetime.now()
            try:
                self.func(*self.args)
                self._decrease_count()
                self.next_schedule = self.standard_interval
                self.next_priority = self.standard_priority
            except AssertionError:
                raise
            except Exception as e:
                self.next_schedule = self.fault_interval
                self.next_priority = self.fault_priority

                if self.fault_callback:
                    self.fault_callback_kwargs['exception'] = e
                    self.fault_callback(**self.fault_callback_kwargs)

        def reschedule(self):
            if self.exhausted:
                return None

            self.scheduler.enter(delay=self.next_schedule,
                                 priority=self.next_priority,
                                 action=self.loop,
                                 argument=())

        def loop(self):
            self.run()
            self.reschedule()

        def _decrease_count(self):
            self.times = max(self.times - 1, -1)
