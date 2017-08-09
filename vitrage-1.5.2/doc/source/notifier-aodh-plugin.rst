===============================
Vitrage Notifier plugins - AODH
===============================

Overview
========
The Evaluator performs root cause analysis on the Vitrage Graph and may determine that an alarm should be created, deleted or otherwise updated.

Other components are notified of such changes by the Vitrage Notifier service. Among others, Vitrage Notifier is responsible for handling Aodh Alarms.

This document describes the implementation of Vitrage Notifier infrastructure and specifically notifying Aodh on Vitrage alarms.

Design
======

::

 +----------+  +-----------+   +------+         +--------+
 | Vitrage  |  | DataSource|   |Graph |         | Message|       +------------------+
 | Evaluator|->| Queue     |-->|      |-------->|  Bus   |------>| Vitrage Notifier |
 +----------+  +-----------+   +------+         |        |       +------------------+
                                                |        |          |        |   |
                                                |        |      +----------+ |   |
                                                |        |      | Aodh     |---+ |
                                                |        |      | notifier |   |----+
                                                |        |   +--| plugin   |   |    |
                                                |        |   |  +----------+   |    |
                                                +--------+   |     +-----------+    |
                                                             |         +------------+
                  +------------------+                       |
                  |   Aodh           |<----------------------+
                  +------------------+

...

DeducedAlarmNotifier class will be subscribed to entity graph notifications. Whenever a vitrage deduced alarm is added to the graph it will post a message to the message bus.
The processor will hold an instance of the DeducedAlarmNotifier class and will subscribe this instance to entity graph notifications.

The VitrageNotifier is a new service that listens to the bus for internal vitrage notifications, then can call all the relevant notifier plugins.

1. Deduced Alarm created by the Evaluator
2. Graph vertex added/updated
3. DeducedAlarmNotifier writes to message bus
4. VitrageNotifierService receives the event and calls all plugins
5. Aodh plugin - using the ceilometer client, creates an event in aodh (with some metadata params in the query)

Deduced Alarms bus notifications
--------------------------------

Vitrage Evaluator will create a deduced alarm, sending it to the data source queue
Vitrage Evaluator will use the **vitrage.graph** message bus topic, and will post messages as follows:

 - message of type ``vitrage.deduced_alarm.activate`` :

   * ``name`` - is the alarm name in vitrage
   * ``severity`` - is the alarm severity
   * ``affected_resource_id`` - is the openstack id of the resource on which the alarm was raised

 - ``vitrage.deduced_alarm.deactivate``

   * ``id`` - is the alarm id

Notifier
========
 - Is a new running service
 - Receives notifications from the message bus
 - Holds instances of all the plugins
 - Upon a received notification, calls 'notify(msg)' for all the plugins
 - Each plugin is responsible of how and whether to process the notification

Aodh Plugin
===========
Vitrage alarms should be reflected as possible in Aodh. The aodh plugin has ceilometer client by which it can send rest calls to aodh

Handle ``vitrage.deduced_alarm.activate``
-----------------------------------------
Create an event alarm with the specified severity, where the alarm name is ``vitrage_alarm_name+resource_id`` so to be unique

 - Message does not contain aodh alarm id:

   * plugin will **create** a new aodh alarm
   * alarm type - event
   * alarm status - alarm
   * query contain resource_id, vitrage_id fields

 - Message contains aodh alarm id

   * plugin will **update** the aodh alarm status to alarm

Handle ``vitrage.deduced_alarm.deactivate``
-------------------------------------------
Delete an event alarm with the specified id

   * message will contain the aodh alarm id - plugin will **update** the alarm status to ok
