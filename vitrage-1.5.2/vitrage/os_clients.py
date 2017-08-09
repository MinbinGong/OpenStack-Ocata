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

import keystoneauth1.identity.v2 as v2
import keystoneauth1.session as kssession
from oslo_config import cfg
from oslo_log import log
from oslo_utils import importutils as utils

from vitrage import keystone_client

LOG = log.getLogger(__name__)

OPTS = [
    cfg.StrOpt('aodh_version', default='2', help='Aodh version'),
    cfg.FloatOpt('nova_version', default='2.11', help='Nova version'),
    cfg.StrOpt('cinder_version', default='2', help='Cinder version'),
    cfg.StrOpt('heat_version', default='1', help='Heat version'),
]

_client_modules = {
    'ceilometer': 'ceilometerclient.client',
    'nova': 'novaclient.client',
    'cinder': 'cinderclient.client',
    'neutron': 'neutronclient.v2_0.client',
    'heat': 'heatclient.v1.client',
}


def driver_module(driver):
    mod_name = _client_modules[driver]
    module = utils.import_module(mod_name)
    return module


def ceilometer_client(conf):
    """Get an instance of ceilometer client"""
    auth_config = conf.service_credentials
    try:
        cm_client = driver_module('ceilometer')
        client = cm_client.get_client(
            version=conf.aodh_version,
            session=keystone_client.get_session(conf),
            region_name=auth_config.region_name,
            interface=auth_config.interface,
        )
        LOG.info('Ceilometer client created')
        return client
    except Exception as e:
        LOG.exception('Create Ceilometer client - Got Exception: %s', e)


def nova_client(conf):
    """Get an instance of nova client"""
    auth_config = conf.service_credentials
    try:
        n_client = driver_module('nova')
        client = n_client.Client(
            version=conf.nova_version,
            session=keystone_client.get_session(conf),
            region_name=auth_config.region_name,
            endpoint_type='publicURL',
        )
        LOG.info('Nova client created')
        return client
    except Exception as e:
        LOG.exception('Create Nova client - Got Exception: %s', e)


def cinder_client(conf):
    """Get an instance of cinder client"""
    auth_config = conf.service_credentials
    try:
        cin_client = driver_module('cinder')
        client = cin_client.Client(
            version=conf.cinder_version,
            session=keystone_client.get_session(conf),
            region_name=auth_config.region_name,
            interface=auth_config.interface,
        )
        LOG.info('Cinder client created')
        return client
    except Exception as e:
        LOG.exception('Create Cinder client - Got Exception: %s', e)


def neutron_client(conf):
    """Get an instance of neutron client"""
    auth_config = conf.service_credentials
    try:
        ne_client = driver_module('neutron')
        client = ne_client.Client(
            session=keystone_client.get_session(conf),
            region_name=auth_config.region_name,
            interface=auth_config.interface,
        )
        LOG.info('Neutron client created')
        return client
    except Exception as e:
        LOG.exception('Create Neutron client - Got Exception: %s', e)


def heat_client(conf):
    """Get an instance of heat client"""
    # auth_config = conf.service_credentials
    try:
        auth = v2.Password(
            auth_url=conf.service_credentials.auth_url + '/v2.0',
            username=conf.service_credentials.username,
            password=conf.service_credentials.password,
            tenant_name=conf.service_credentials.project_name)
        session = kssession.Session(auth=auth)
        endpoint = session.get_endpoint(service_type='orchestration',
                                        interface='publicURL')
        he_client = driver_module('heat')
        client = he_client.Client(session=session, endpoint=endpoint)
        LOG.info('Heat client created')
        return client
    except Exception as e:
        LOG.exception('Create Heat client - Got Exception: %s', e)
