# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2014 SoftLayer Technologies, Inc.
# Copyright 2015 Mirantis, Inc
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
System-level utilities and helper functions.
"""

import errno

from eventlet.green import socket

import functools
import os
import platform
import re
import stevedore
import subprocess
import sys
import uuid

from OpenSSL import crypto
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import excutils
from oslo_utils import netutils
from oslo_utils import uuidutils
import six
from webob import exc

from searchlight.common import exception
from searchlight.i18n import _, _LE, _LW
from searchlight import plugin

LOG = logging.getLogger(__name__)
CONF = cfg.CONF

FEATURE_BLACKLIST = ['content-length', 'content-type', 'x-image-meta-size']
SEARCHLIGHT_TEST_SOCKET_FD_STR = 'SEARCHLIGHT_TEST_SOCKET_FD'
DOT_REPLACEMENT_KEY = '++'


def safe_mkdirs(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def safe_remove(path):
    try:
        os.remove(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


class PrettyTable(object):
    """Creates an ASCII art table for use in bin/searchlight

    Example:

        ID  Name              Size         Hits
        --- ----------------- ------------ -----
        122 image                       22     0
    """
    def __init__(self):
        self.columns = []

    def add_column(self, width, label="", just='l'):
        """Add a column to the table

        :param width: number of characters wide the column should be
        :param label: column heading
        :param just: justification for the column, 'l' for left,
                     'r' for right
        """
        self.columns.append((width, label, just))

    def make_header(self):
        label_parts = []
        break_parts = []
        for width, label, just in self.columns:
            # NOTE(sirp): headers are always left justified
            label_part = self._clip_and_justify(label, width, 'l')
            label_parts.append(label_part)

            break_part = '-' * width
            break_parts.append(break_part)

        label_line = ' '.join(label_parts)
        break_line = ' '.join(break_parts)
        return '\n'.join([label_line, break_line])

    def make_row(self, *args):
        row = args
        row_parts = []
        for data, (width, label, just) in zip(row, self.columns):
            row_part = self._clip_and_justify(data, width, just)
            row_parts.append(row_part)

        row_line = ' '.join(row_parts)
        return row_line

    @staticmethod
    def _clip_and_justify(data, width, just):
        # clip field to column width
        clipped_data = str(data)[:width]

        if just == 'r':
            # right justify
            justified = clipped_data.rjust(width)
        else:
            # left justify
            justified = clipped_data.ljust(width)

        return justified


def get_terminal_size():

    def _get_terminal_size_posix():
        import fcntl
        import struct
        import termios

        height_width = None

        try:
            height_width = struct.unpack('hh', fcntl.ioctl(sys.stderr.fileno(),
                                         termios.TIOCGWINSZ,
                                         struct.pack('HH', 0, 0)))
        except Exception:
            pass

        if not height_width:
            try:
                p = subprocess.Popen(['stty', 'size'],
                                     shell=False,
                                     stdout=subprocess.PIPE,
                                     stderr=open(os.devnull, 'w'))
                result = p.communicate()
                if p.returncode == 0:
                    return tuple(int(x) for x in result[0].split())
            except Exception:
                pass

        return height_width

    def _get_terminal_size_win32():
        try:
            from ctypes import create_string_buffer
            from ctypes import windll
            handle = windll.kernel32.GetStdHandle(-12)
            csbi = create_string_buffer(22)
            res = windll.kernel32.GetConsoleScreenBufferInfo(handle, csbi)
        except Exception:
            return None
        if res:
            import struct
            unpack_tmp = struct.unpack("hhhhHhhhhhh", csbi.raw)
            (bufx, bufy, curx, cury, wattr,
             left, top, right, bottom, maxx, maxy) = unpack_tmp
            height = bottom - top + 1
            width = right - left + 1
            return (height, width)
        else:
            return None

    def _get_terminal_size_unknownOS():
        raise NotImplementedError

    func = {'posix': _get_terminal_size_posix,
            'win32': _get_terminal_size_win32}

    height_width = func.get(platform.os.name, _get_terminal_size_unknownOS)()

    if height_width is None:
        raise exception.Invalid()

    for i in height_width:
        if not isinstance(i, int) or i <= 0:
            raise exception.Invalid()

    return height_width[0], height_width[1]


def mutating(func):
    """Decorator to enforce read-only logic"""
    @functools.wraps(func)
    def wrapped(self, req, *args, **kwargs):
        if req.context.read_only:
            msg = "Read-only access"
            LOG.debug(msg)
            raise exc.HTTPForbidden(msg, request=req,
                                    content_type="text/plain")
        return func(self, req, *args, **kwargs)
    return wrapped


def setup_remote_pydev_debug(host, port):
    error_msg = _LE('Error setting up the debug environment. Verify that the'
                    ' option pydev_worker_debug_host is pointing to a valid '
                    'hostname or IP on which a pydev server is listening on'
                    ' the port indicated by pydev_worker_debug_port.')

    try:
        try:
            from pydev import pydevd
        except ImportError:
            import pydevd

        pydevd.settrace(host,
                        port=port,
                        stdoutToServer=True,
                        stderrToServer=True)
        return True
    except Exception:
        with excutils.save_and_reraise_exception():
            LOG.exception(error_msg)


def validate_key_cert(key_file, cert_file):
    try:
        error_key_name = "private key"
        error_filename = key_file
        with open(key_file, 'r') as keyfile:
            key_str = keyfile.read()
        key = crypto.load_privatekey(crypto.FILETYPE_PEM, key_str)

        error_key_name = "certificate"
        error_filename = cert_file
        with open(cert_file, 'r') as certfile:
            cert_str = certfile.read()
        cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_str)
    except IOError as ioe:
        raise RuntimeError(_("There is a problem with your %(error_key_name)s "
                             "%(error_filename)s.  Please verify it."
                             "  Error: %(ioe)s") %
                           {'error_key_name': error_key_name,
                            'error_filename': error_filename,
                            'ioe': ioe})
    except crypto.Error as ce:
        raise RuntimeError(_("There is a problem with your %(error_key_name)s "
                             "%(error_filename)s.  Please verify it. OpenSSL"
                             " error: %(ce)s") %
                           {'error_key_name': error_key_name,
                            'error_filename': error_filename,
                            'ce': ce})

    try:
        data = uuidutils.generate_uuid()
        digest = CONF.digest_algorithm
        if digest == 'sha1':
            LOG.warning(
                _LW('The FIPS (FEDERAL INFORMATION PROCESSING STANDARDS)'
                    ' state that the SHA-1 is not suitable for'
                    ' general-purpose digital signature applications (as'
                    ' specified in FIPS 186-3) that require 112 bits of'
                    ' security. The default value is sha1 in Kilo for a'
                    ' smooth upgrade process, and it will be updated'
                    ' with sha256 in next release(L).'))
        out = crypto.sign(key, data, digest)
        crypto.verify(cert, out, data, digest)
    except crypto.Error as ce:
        raise RuntimeError(_("There is a problem with your key pair.  "
                             "Please verify that cert %(cert_file)s and "
                             "key %(key_file)s belong together.  OpenSSL "
                             "error %(ce)s") % {'cert_file': cert_file,
                                                'key_file': key_file,
                                                'ce': ce})


def get_test_suite_socket():
    global SEARCHLIGHT_TEST_SOCKET_FD_STR
    if SEARCHLIGHT_TEST_SOCKET_FD_STR in os.environ:
        fd = int(os.environ[SEARCHLIGHT_TEST_SOCKET_FD_STR])
        sock = socket.fromfd(fd, socket.AF_INET, socket.SOCK_STREAM)
        if six.PY2:
            sock = socket.SocketType(_sock=sock)
        sock.listen(CONF.api.backlog)
        del os.environ[SEARCHLIGHT_TEST_SOCKET_FD_STR]
        os.close(fd)
        return sock
    return None


def is_uuid_like(val):
    """Returns validation of a value as a UUID.

    For our purposes, a UUID is a canonical form string:
    aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa
    """
    try:
        return str(uuid.UUID(val)) == val
    except (TypeError, ValueError, AttributeError):
        return False


def is_valid_hostname(hostname):
    """Verify whether a hostname (not an FQDN) is valid."""
    return re.match('^[a-zA-Z0-9-]+$', hostname) is not None


def is_valid_fqdn(fqdn):
    """Verify whether a host is a valid FQDN."""
    return re.match('^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', fqdn) is not None


def parse_valid_host_port(host_port):
    """
    Given a "host:port" string, attempts to parse it as intelligently as
    possible to determine if it is valid. This includes IPv6 [host]:port form,
    IPv4 ip:port form, and hostname:port or fqdn:port form.

    Invalid inputs will raise a ValueError, while valid inputs will return
    a (host, port) tuple where the port will always be of type int.
    """

    try:
        try:
            host, port = netutils.parse_host_port(host_port)
        except Exception:
            raise ValueError(_('Host and port "%s" is not valid.') % host_port)

        if not netutils.is_valid_port(port):
            raise ValueError(_('Port "%s" is not valid.') % port)

        # First check for valid IPv6 and IPv4 addresses, then a generic
        # hostname. Failing those, if the host includes a period, then this
        # should pass a very generic FQDN check. The FQDN check for letters at
        # the tail end will weed out any hilariously absurd IPv4 addresses.

        if not (netutils.is_valid_ipv6(host) or netutils.is_valid_ipv4(host) or
                is_valid_hostname(host) or is_valid_fqdn(host)):
            raise ValueError(_('Host "%s" is not valid.') % host)

    except Exception as ex:
        raise ValueError(_('%s '
                           'Please specify a host:port pair, where host is an '
                           'IPv4 address, IPv6 address, hostname, or FQDN. If '
                           'using an IPv6 address, enclose it in brackets '
                           'separately from the port (i.e., '
                           '"[fe80::a:b:c]:9876").') % ex)

    return (host, int(port))


try:
    REGEX_4BYTE_UNICODE = re.compile(u'[\U00010000-\U0010ffff]')
except re.error:
    # UCS-2 build case
    REGEX_4BYTE_UNICODE = re.compile(u'[\uD800-\uDBFF][\uDC00-\uDFFF]')


def no_4byte_params(f):
    """
    Checks that no 4 byte unicode characters are allowed
    in dicts' keys/values and string's parameters
    """
    def wrapper(*args, **kwargs):

        def _is_match(some_str):
            return (isinstance(some_str, unicode) and
                    REGEX_4BYTE_UNICODE.findall(some_str) != [])

        def _check_dict(data_dict):
            # a dict of dicts has to be checked recursively
            for key, value in data_dict.iteritems():
                if isinstance(value, dict):
                    _check_dict(value)
                else:
                    if _is_match(key):
                        msg = _("Property names can't contain 4 byte unicode.")
                        raise exception.Invalid(msg)
                    if _is_match(value):
                        msg = (_("%s can't contain 4 byte unicode characters.")
                               % key.title())
                        raise exception.Invalid(msg)

        for data_dict in [arg for arg in args if isinstance(arg, dict)]:
            _check_dict(data_dict)
        # now check args for str values
        for arg in args:
            if _is_match(arg):
                msg = _("Param values can't contain 4 byte unicode.")
                raise exception.Invalid(msg)
        # check kwargs as well, as params are passed as kwargs via
        # registry calls
        _check_dict(kwargs)
        return f(*args, **kwargs)
    return wrapper


def stash_conf_values():
    """
    Make a copy of some of the current global CONF's settings.
    Allows determining if any of these values have changed
    when the config is reloaded.
    """
    conf = {}
    conf['bind_host'] = CONF.api.bind_host
    conf['bind_port'] = CONF.api.bind_port
    conf['tcp_keepidle'] = CONF.api.cert_file
    conf['backlog'] = CONF.api.backlog
    conf['key_file'] = CONF.api.key_file
    conf['cert_file'] = CONF.api.cert_file

    return conf


def register_plugin_opts():
    plugin.Plugin.register_cfg_opts('searchlight.index_backend')


def get_search_plugins():
    namespace = 'searchlight.index_backend'
    ext_manager = stevedore.extension.ExtensionManager(
        namespace, invoke_on_load=True)
    plugins = {plugin.obj.get_document_type(): plugin
               for plugin in ext_manager.extensions if plugin.obj.enabled}

    # Set up any parent/child relationships. Although this may be called
    # multiple times, in practice get_search_plugins is rarely called.
    # Unfortunately there's nowhere better to put this; stevedore instantiates
    # the plugins before we get to them
    for plugin_type, loaded_plugin in plugins.items():
        parent_type = loaded_plugin.obj.parent_plugin_type()
        if parent_type:
            LOG.debug("Setting up link between parent (%s) and child (%s)"
                      % (parent_type, plugin_type))
            parent_plugin = plugins.get(parent_type, None)
            if not parent_plugin:
                raise exception.SearchlightException(
                    "Error loading %(plugin_type)s; expected parent plugin "
                    "%(parent_type)s is not loaded" %
                    {"plugin_type": plugin_type, "parent_type": parent_type})

            loaded_plugin.obj.register_parent(parent_plugin.obj)

    return plugins


def expand_type_matches(types, document_types):
    """Returns a list that will be at least the length of `types`. If an item
    ends with a wildcard character and matches at least one plugin document
    type it'll be replaced with the matches in the return list.
     """
    expanded_types = []
    for _type in types:
        if _type.endswith('*'):
            matches = [doc_type for doc_type in document_types
                       if doc_type.startswith(_type[:-1])]
            if matches:
                expanded_types.extend(matches)
                continue

        # If we got here, either wasn't a wildcard or didn't match anything
        expanded_types.append(_type)

    return expanded_types


def _convert_field(document, original, current):
    """Convert field name by replacing original string with current"""
    if isinstance(document, dict):
        for k, v in six.iteritems(document):
            if isinstance(v, list) or isinstance(v, dict):
                _convert_field(v, original, current)
            if original in k:
                document.pop(k)
                document[k.replace(original, current)] = v
    elif isinstance(document, list):
        for doc in document:
            if isinstance(doc, list) or isinstance(doc, dict):
                _convert_field(doc, original, current)


def replace_dots_in_field_names(document):
    _convert_field(document, '.', DOT_REPLACEMENT_KEY)


def restore_dots_in_field_names(document):
    _convert_field(document, DOT_REPLACEMENT_KEY, '.')
