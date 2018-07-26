# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import unittest
import mock


with mock.patch('charmhelpers.core.hookenv.metadata') as _meta:
    _meta.return_Value = 'ss'
    import requires


_hook_args = {}

TO_PATCH = [
    'clear_flag',
    'set_flag',
]


def mock_hook(*args, **kwargs):

    def inner(f):
        # remember what we were passed.  Note that we can't actually determine
        # the class we're attached to, as the decorator only gets the function.
        _hook_args[f.__name__] = dict(args=args, kwargs=kwargs)
        return f
    return inner


class _unit_mock:
    def __init__(self, unit_name, received=None):
        self.unit_name = unit_name
        self.received = received or {}


class _relation_mock:
    def __init__(self, application_name=None, units=None):
        self.to_publish_raw = {}
        self.application_name = application_name
        self.units = units


class TestCellRequires(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._patched_hook = mock.patch('charms.reactive.when', mock_hook)
        cls._patched_hook_started = cls._patched_hook.start()
        # force requires to rerun the mock_hook decorator:
        # try except is Python2/Python3 compatibility as Python3 has moved
        # reload to importlib.
        try:
            reload(requires)
        except NameError:
            import importlib
            importlib.reload(requires)

    @classmethod
    def tearDownClass(cls):
        cls._patched_hook.stop()
        cls._patched_hook_started = None
        cls._patched_hook = None
        # and fix any breakage we did to the module
        try:
            reload(requires)
        except NameError:
            import importlib
            importlib.reload(requires)

    def patch(self, method):
        _m = mock.patch.object(self.obj, method)
        _mock = _m.start()
        self.addCleanup(_m.stop)
        return _mock

    def setUp(self):
        self.cr = requires.CellRequires('some-relation', [])
        self._patches = {}
        self._patches_start = {}
        self.obj = requires
        for method in TO_PATCH:
            setattr(self, method, self.patch(method))

    def tearDown(self):
        self.cr = None
        for k, v in self._patches.items():
            v.stop()
            setattr(self, k, None)
        self._patches = None
        self._patches_start = None

    def patch_kr(self, attr, return_value=None):
        mocked = mock.patch.object(self.cr, attr)
        self._patches[attr] = mocked
        started = mocked.start()
        started.return_value = return_value
        self._patches_start[attr] = started
        setattr(self, attr, started)

    def test_registered_hooks(self):
        # test that the decorators actually registered the relation
        # expressions that are meaningful for this interface: this is to
        # handle regressions.
        # The keys are the function names that the hook attaches to.
        hook_patterns = {
            'data_changed': ('endpoint.{endpoint_name}.changed', ),
            'joined': ('endpoint.{endpoint_name}.joined', ),
            'broken': ('endpoint.{endpoint_name}.joined', ),
        }
        for k, v in _hook_args.items():
            self.assertEqual(hook_patterns[k], v['args'])

    def test_date_changed(self):
        mock_aju = mock.MagicMock()
        mock_aju.received = {'network_manager': 'nm'}
        self.cr._all_joined_units = mock_aju
        self.cr.data_changed()
        self.set_flag.assert_called_once_with('some-relation.available')

    def test_date_changed_missing_data(self):
        mock_aju = mock.MagicMock()
        mock_aju.received = {}
        self.cr._all_joined_units = mock_aju
        self.cr.data_changed()
        self.assertFalse(self.set_flag.called)

    def test_broken(self):
        self.cr.broken()
        self.clear_flag.assert_called_once_with('some-relation.available')

    def test_joined(self):
        self.cr.joined()
        self.set_flag.assert_called_once_with('some-relation.connected')

    def test_send_cell_data(self):
        mock_rel1 = _relation_mock()
        mock_rel2 = _relation_mock()
        self.cr._relations = [mock_rel1, mock_rel2]
        self.cr.send_cell_data(
            'cell2',
            'rabbitmq-server-cell2',
            'mysql-cell2')
        expect = {
            'amqp-service': 'rabbitmq-server-cell2',
            'db-service': 'mysql-cell2',
            'cell-name': 'cell2'}
        self.assertEqual(mock_rel1.to_publish_raw, expect)
        self.assertEqual(mock_rel2.to_publish_raw, expect)

    def test_get_settings(self):
        mock_aju = mock.MagicMock()
        mock_aju.received = {
            'key1': 'value1',
            'key2': 'value2',
            'key3': 'value3'}
        self.cr._all_joined_units = mock_aju
        self.assertEqual(
            self.cr.get_settings(['key1', 'key3']),
            {'key1': 'value1', 'key3': 'value3'})

    def setup_rdata(self):
        mock_aju = mock.MagicMock()
        mock_aju.received = {
            'enable_serial_console': True,
            'serial_console_base_url': 'http://serialconsole',
            'network_manager': 'vTRManager',
            'quantum_plugin': 'vTokenRing',
            'quantum_security_groups': 'no',
            'quantum_url': 'http://bob:345/dddd/',
            'region': 'Region12',
            'volume_service': 'cinder',
            'restart_trigger': 'a-uuid',
            'ec2_host': 'http://ec2host'}
        self.cr._all_joined_units = mock_aju

    def test_get_console_data(self):
        self.setup_rdata()
        self.assertEqual(
            self.cr.get_console_data(),
            {
                'enable_serial_console': True,
                'serial_console_base_url': 'http://serialconsole'})

    def test_get_network_data(self):
        self.setup_rdata()
        self.assertEqual(
            self.cr.get_network_data(),
            {
                'network_manager': 'vTRManager',
                'quantum_plugin': 'vTokenRing',
                'quantum_security_groups': 'no',
                'quantum_url': 'http://bob:345/dddd/'})

    def test_get_region(self):
        self.setup_rdata()
        self.assertEqual(
            self.cr.get_region(),
            {'region': 'Region12'})

    def test_get_volume_data(self):
        self.setup_rdata()
        self.assertEqual(
            self.cr.get_volume_data(),
            {'volume_service': 'cinder'})

    def test_get_ec2_data(self):
        self.setup_rdata()
        self.assertEqual(
            self.cr.get_ec2_data(),
            {'ec2_host': 'http://ec2host'})

    def test_get_restart_trigger(self):
        self.setup_rdata()
        self.assertEqual(
            self.cr.get_restart_trigger(),
            {'restart_trigger': 'a-uuid'})
