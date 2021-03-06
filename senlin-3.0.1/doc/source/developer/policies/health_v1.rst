..
  Licensed under the Apache License, Version 2.0 (the "License"); you may
  not use this file except in compliance with the License. You may obtain
  a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
  License for the specific language governing permissions and limitations
  under the License.


==================
Health Policy V1.0
==================

The health policy is designed to automate the failure detection and recovery
process for a cluster.


Applicable Profile Types
~~~~~~~~~~~~~~~~~~~~~~~~

The policy is designed to handle both ``os.nova.server`` and ``os.heat.stack``
profile types.


Actions Handled
~~~~~~~~~~~~~~~

The policy is capable of handling the following actions:

- ``CLUSTER_RECOVER``: an action that carries some optional parameters as its
  inputs. The parameters are specific to the profile type of the target
  cluster.

- ``CLUSTER_DEL_NODES``: an action that carries a list value named
  ``candidates`` in its ``inputs`` value.

- ``CLUSTER_SCALE_IN``: an action that carries an optional integer value named
  ``count`` in its ``inputs`` value.

- ``CLUSTER_RESIZE``: an action that carries various key-value pairs as
  arguments to the action in its ``inputs`` value.

- ``NODE_DELETE``: an action that has a node associated with it. This action
  has to be originated from a RPC request directly so that it will be
  processed by the health policy.

The policy will be checked **BEFORE** a ``CLUSTER_RECOVER`` action is executed.
It will derive the appropriate inputs to the action based on the policy's
properties.

The policy will be checked **BEFORE** and **AFTER** any one of the
``CLUSTER_DEL_NODES``, ``CLUSTER_SCALE_IN``, ``CLUSTER_RESIZE`` and the
``NODE_DELETE`` action is executed. Under the condition that any of these
actions are originated from RPC requests, Senlin is aware of the fact that
a cluster is losing node member(s) because of a normal cluster membership
management operation initiated by users rather than unexpected node failures.
The health policy will temporarily disable the *health manager* function on
the cluster in question and re-enable the health management after the action
has completed.

The health policy can be treated as an interface for the *health manager*
engine running inside the ``senlin-engine`` process. Its specification
contains two main "sections", ``detection`` and ``recovery``, each of which
specifies how to detect node failures and how to recover a node to a healthy
status respectively.


Failure Detection
~~~~~~~~~~~~~~~~~

The health policy is designed to be flexible regarding node failure detection.
The current vision is that the health policy will support following types
of failure detection:

* ``NODE_STATUS_POLLING``: the *health manager* periodically polls a cluster
  and check if there are nodes inactive.

* ``LIFECYCLE_EVENTS``: the *health manager* listens to event notifications
  sent by the backend service (e.g. nova-compute).

* ``LB_STATUS_POLLING``: the *health manager* periodically polls the load
  balancer (if any) and see if any node has gone offline.

The third option above (``LB_STATUS_POLLING``) is not usable yet due to an
outstanding issue in the LBaaS service. But we are still tracking its progress
considering that metrics from the load-balancer is more trust-worthy and more
useful because they originate from the data plane rather than the control
plane.

Yet another option regarding load-balancer based health detection is to have
the load-balancer emit event notifications when node status changes. This is
also an ongoing work which may take some time to land.


Proactive Node Status Polling
-----------------------------

The most straight-foward way of node failure detection is by checking the
backend service about the status of the physical resource represented by a
node. If the ``type`` of ``detection`` is set to "``NODE_STATUS_POLLING``"
(optionally, with an ``interval`` value specified), the *health manager* will
periodically check the resource status by querying the backend service and see
if the resource is active.  Below is a sample configuration::

  type: senlin.policy.health
  version: 1.0
  properties:
    detection:
      type: NODE_STATUS_POLLING
      options:
        internal: 120

    ...

**NOTE**: The current polling logic is only about checking with the backend
service whether a resource is in "ACTIVE" status. However, in future, this may
get extended to having the *health manager* ping the IP address of a nova
server or posting a "GET" request to a specific URL. We believe such
extensions can better reveal whether a specific node is operating.

Once such a policy object is attached to a cluster, Senlin registers the
cluster to the *health manager* engine for failure detection, i.e., node
health checking. A thread is created to issue a ``CLUSTER_CHECK`` RPC request
to the ``senlin-engine`` periodically at the specified interval. The
``CLUSTER_CHECK`` action only refreshes the status of each and every node in
the cluster.

When one of the ``senlin-engine`` services is restarted, a new *health manager*
engine will be launched. This new engine will check the database and see if
there are clusters which have health policies attached and thus having its
health status maintained by a *health manager* that is no longer alive. The
new *health manager* will pick up these clusters for health management.


Listening to Event Notifications
--------------------------------

For some profile types (currently ``os.nova.server``), the backend service may
emit an event notification on the control plane message bus. These events are
more economic ways for node failure detection, assuming that all kinds of
status changes will be captured and reported by the backend service. Actually,
we have verified that most lifecycle events related to a VM server are already
captured and reported by Nova. For other profile types such as
``os.heat.stack``, there also exists such a possibility although based on our
knowledge Heat cannot detect all stack failures.

Event listening is a cheaper way for node failure detection when compared to
the status polling approach described above. To instruct the *health manager*
to listen to event notifications, users can attach their cluster(s) a health
policy which looks like the following example::

  type: senlin.policy.health
  version: 1.0
  properties:
    detection:
      type: LIFECYCLE_EVENTS

    ...

When such a policy is attached to a cluster, Senlin registers the cluster to
the *health manager* engine for failure detection, i.e., node health checking.
A listener thread is created to listen to events that indicate certain node
has failed.  For nova server nodes, the current implementation treats all of
the following event types as indication of node failures:

* ``compute.instance.delete.end``: A server has been accidentally deleted.
* ``compute.instance.pause.end``: A server has been accidentally paused.
* ``compute.instance.power_off.end``: A server has been stopped accidentally.
* ``compute.instance.rebuild.error``: A server rebuild has failed.
* ``compute.instance.shutdown.end``: A server has been shut down for unknown
  reasons.
* ``compute.instance.soft_delete.end``: A server has been soft deleted.

When any one of such an event is heard by the listener thread, it will issue
a ``NODE_RECOVER`` RPC request to the senlin-engine service. For the health
policy to make a smarter decision on the proper recover operation, the RPC
request is augmented with some parameters as hints to the recovery operation
as exemplified below::

  {
    "event": "SHUTDOWN",
    "state": "shutdown",
    "instance_id": "449ad837-3db2-4aa9-b324-ecd28e14ab14",
    "timestamp": "2016-11-27T12:10:58Z",
    "publisher": "nova-compute:node1",
  }

Ideally, a health management solution can react differently based on the
different types of failures detected. For example, a server stopped by accident
can be simply recovered by start it again; a paused server can be unpaused
quickly instead of being recreated.

When one of the ``senlin-engine`` services is restarted, a new *health manager*
engine will be launched. This new engine will check the database and see if
there are clusters which have health policies attached and thus having its
health status maintained by a *health manager* that is no longer alive. The
new *health manager* will pick up these clusters for health management.


Recovery Actions
~~~~~~~~~~~~~~~~

The value of the recovery ``actions`` key for ``recovery`` is modeled as a
list, each of which specifies an action to try. The list of actions are to be
adjusted by the policy before passing on to a base ``Profile`` for actual
execution. An example (imaginary) list of actions is shown below::

  type: senlin.policy.health
  version: 1.0
  properties:
    ...
    recovery:
      actions:
        - name: REBOOT
          params:
            type: soft
        - name: REBUILD
        - name: my_evacuation_workflow
          type: MISTRAL_WORKFLOW
          params:
            node_id: {{ node.physicalid }}

The above specification basically tells Senlin engine to try a list of
recovery actions one by one. The first thing to try is to "reboot" (an
operation only applicable on a Nova server) the failed node in question. If
that didn't solve the problem, the engine is expected to "rebuild" (also a
Nova server specific verb) the failed node. If this cannot bring the node back
to healthy status, the engine should execute a Mistral workflow named
"``my_evacuation_workflow``" and pass in the physical ID of the node.

The health policy is triggered when a ``CLUSTER_RECOVER`` action is to be
executed. Using the above example, the policy object will fill in the ``data``
field of the action object with the following content::

   {
     "health": {
       "recover_action": [
         {
           "name": "REBOOT",
           "params": {
             "type": "soft"
           }
         },
         {
           "name": "REBUILD"
         },
         {
           "name": "my_evacuation_workflow",
           "type": "MISTRAL_WORKFLOW",
           "params": {
             "node_id": "7a753f4b-417d-4c10-8065-681f60db0c9a"
           }
         }
       ]
       ...
     }
   }

This action customization is eventually passed on to the ``Profile`` base
class where the actual actions are performed.

**NOTE**: Currently, we only support a single action in the list. The support
to Mistral workflow is also an ongoing work.


Default Recovery Action
-----------------------

Since Senlin is designed to manage different types of resources, each resource
type, i.e. :term:`profile type`, may support different sets of operations that
can be used for failure recovery.

A more practical and more general operation to recover a failed resource is to
delete the old one followed by creating a new one, thus a ``RECREATE``
operation. Note that the ``RECREATE`` action is although generic enough, it
may and may not be what users want. For example, there is not guarantee that a
recreated Nova server will preserve its physical ID or its IP address. The
temporary status of the original server will be lost for sure.


Profile-specific Recovery Actions
---------------------------------

Each profile type supports a unique set of operations, some of which are
relevant to failure recovery. For example, a Nova server may support many
operations that can be used for failure recovery, a Heat stack may support
only the ``STACK_UPDATE`` operation for recovery. This set of actions that can
be specified for recovery is profile specific, thus an important part for the
policy to check and validate.


External Recovery Actions
-------------------------

In real-life deployments, there are use cases where a simple recovery of a
node itself is not sufficient to bring back the business services or
applications that were running on those nodes. There are other use cases where
appropriate actions must be taken on the storage and/or network used for a
full failure recovery. These are the triggers for the Senlin team to bring in
support to Mistral workflows as special actions.

The current design is to allow for a mixture of built-in recovery actions and
user provided workflows. In the forseeable future, Senlin does not manage the
workflows to be executed and the team has no plan to support the debugging of
workflow executions. Users have to make sure their workflows are doing things
they want.


Fencing Support
~~~~~~~~~~~~~~~

The term "fencing" is used to describe the operations that make sure a
seemingly failed resource is dead for sure. This is a very important aspect in
all high-availability solutions. Take a Nova server failure as an example,
there are many causes which can lead the server into an inactive status. A
physical host crash, a network connection breakage etc. can all result in a
node unreachable. From Nova controller's perspective, it may appear that the
host has gone offline, however, what really happened could be just the
management network is experiencing some problems. The host is actually still
there, all the VM instances on it are still active, which means they are still
processing requests and they are still using the IP addresses allocated to
them by a DHCP server.

There are many such cases where a seemingly inactive node is still working and
these nodes will bring the whole cluster into unpredictable status if we only
attempt an immature recovery action without considering the possibility that
the nodes are still alive.

Considering this, we are working on modeling and implementing support to
fencing in the health policy.
