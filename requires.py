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

import socket
from urllib.parse import urlparse
import uuid

from charmhelpers.core import hookenv

from charms.reactive import set_flag, clear_flag
from charms.reactive import Endpoint
from charms.reactive import when_any, when_not, when


class CellRequires(Endpoint):

    @when('endpoint.{endpoint_name}.changed')
    def data_changed(self):
        if self.all_joined_units.received.get('network_manager'):
            set_flag(self.expand_name('{endpoint_name}.available'))

    @when_not('endpoint.{endpoint_name}.joined')
    def broken(self):
        clear_flag(self.expand_name('{endpoint_name}.available'))

    @when('endpoint.{endpoint_name}.joined')
    def joined(self):
        print("CellRequires")
        set_flag(self.expand_name('{endpoint_name}.connected'))

    def send_cell_data(self, cell_name, amqp_svc_name, db_svc_name):
        for relation in self.relations:
            relation.to_publish_raw['amqp-service'] = amqp_svc_name
            relation.to_publish_raw['db-service'] = db_svc_name
            relation.to_publish_raw['cell-name'] = cell_name

    def get_settings(self, keys):
        settings = {}
        for key in keys:
            settings[key] = self.all_joined_units.received.get(key)
        return settings

    def get_console_data(self):
        return self.get_settings(
            ['enable_serial_console', 'serial_console_base_url'])

    def get_network_data(self):
        return self.get_settings(
            ['network_manager', 'quantum_plugin', 'quantum_security_groups',
             'quantum_url'])

    def get_region(self):
        return self.get_settings(['region'])

    def get_volume_data(self):
        return self.get_settings(['volume_service'])

    def get_ec2_data(self):
        return self.get_settings(['ec2_host'])
