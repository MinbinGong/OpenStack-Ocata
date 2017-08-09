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

import logging
import os
import pecan

from oslo_config import cfg
from oslo_log import log
# noinspection PyPackageRequirements
from paste import deploy
from werkzeug import serving

from vitrage.api import hooks
# noinspection PyProtectedMember
from vitrage.i18n import _LI
# noinspection PyProtectedMember
from vitrage.i18n import _LW
from vitrage import service

LOG = log.getLogger(__name__)

PECAN_CONFIG = {
    'app': {
        'root': 'vitrage.api.controllers.root.RootController',
        'modules': ['vitrage.api'],
    },
}


def setup_app(pecan_config=PECAN_CONFIG, conf=None):
    if conf is None:
        raise RuntimeError('Config is actually mandatory')
    app_hooks = [hooks.ConfigHook(conf),
                 hooks.TranslationHook(),
                 hooks.RPCHook(conf),
                 hooks.ContextHook()]

    pecan.configuration.set_config(dict(pecan_config), overwrite=True)
    pecan_debug = conf.api.pecan_debug
    if conf.api.workers != 1 and pecan_debug:
        pecan_debug = False
        LOG.warning(_LW('pecan_debug cannot be enabled, if workers is > 1, '
                        'the value is overridden with False'))

    app = pecan.make_app(
        pecan_config['app']['root'],
        debug=pecan_debug,
        hooks=app_hooks,
        guess_content_type_from_ext=False
    )

    return app


def load_app(conf):
    # Build the WSGI app
    cfg_file = None
    cfg_path = conf.api.paste_config
    if not os.path.isabs(cfg_path):
        cfg_file = conf.find_file(cfg_path)
    elif os.path.exists(cfg_path):
        cfg_file = cfg_path

    if not cfg_file:
        raise cfg.ConfigFilesNotFoundError([conf.api.paste_config])
    LOG.info(_LI('Full WSGI config used: %s') % cfg_file)
    return deploy.loadapp("config:" + cfg_file)


def build_server(conf):
    app = load_app(conf)
    # Create the WSGI server and start it
    host, port = conf.api.host, conf.api.port

    LOG.info(_LI('Starting server in PID %s') % os.getpid())
    LOG.info(_LI('Configuration:'))
    conf.log_opt_values(LOG, logging.INFO)

    if host == '0.0.0.0':
        LOG.info(_LI(
            'serving on 0.0.0.0:%(port)s, view at http://127.0.0.1:%(port)s')
            % ({'port': port}))
    else:
        LOG.info(_LI('serving on http://%(host)s:%(port)s') % (
            {'host': host, 'port': port}))

    serving.run_simple(host, port,
                       app, processes=conf.api.workers)


def _app():
    conf = service.prepare_service()
    return setup_app(conf=conf)


def app_factory(global_config, **local_conf):
    return _app()
