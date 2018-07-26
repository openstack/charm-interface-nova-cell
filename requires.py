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

from charms.reactive import set_flag, clear_flag
from charms.reactive import Endpoint
from charms.reactive import when_not, when


class CellRequires(Endpoint):

    @when('endpoint.{endpoint_name}.changed')
    def data_changed(self):
        """Set flag to indicate to charm relation data has changed."""
        if self.all_joined_units.received.get('network_manager'):
            set_flag(self.expand_name('{endpoint_name}.available'))

    @when_not('endpoint.{endpoint_name}.joined')
    def broken(self):
        """Remove flag to indicate to charm relation has gone.."""
        clear_flag(self.expand_name('{endpoint_name}.available'))

    @when('endpoint.{endpoint_name}.joined')
    def joined(self):
        """Set flag to indicate to charm relation has been joined."""
        set_flag(self.expand_name('{endpoint_name}.connected'))

    def send_cell_data(self, cell_name, amqp_svc_name, db_svc_name):
        """Send compute nodes data relating to network setup.

        :param cell_name: Name of the cell this controller is associated with.
        :type cell_name: str
        :param amqp_svc_name: URL for this cells nova message broker.
        :type amqp_svc_name: str
        :param db_svc_name: URL for this cells nova db.
        :type db_svc_name: str
        """
        for relation in self.relations:
            relation.to_publish_raw['amqp-service'] = amqp_svc_name
            relation.to_publish_raw['db-service'] = db_svc_name
            relation.to_publish_raw['cell-name'] = cell_name

    def get_settings(self, keys):
        """Retrieve setting(s) from remote units.

        :param keys: List of keys and their vaules to retrieve.
        :type keys: str
        :returns: Requested key value pairs.
        :rtype: dict
        """
        settings = {}
        for key in keys:
            settings[key] = self.all_joined_units.received.get(key)
        return settings

    def get_console_data(self):
        """Retrieve console settings from remote application.

        :returns: console settings
        :rtype: dict
        """
        return self.get_settings(
            ['enable_serial_console', 'serial_console_base_url'])

    def get_network_data(self):
        """Retrieve network settings from remote application.

        :returns: network settings
        :rtype: dict
        """
        return self.get_settings(
            ['network_manager', 'quantum_plugin', 'quantum_security_groups',
             'quantum_url'])

    def get_region(self):
        """Retrieve region settings from remote application.

        :returns: region settings
        :rtype: dict
        """
        return self.get_settings(['region'])

    def get_volume_data(self):
        """Retrieve volume settings from remote application.

        :returns: volume settings
        :rtype: dict
        """
        return self.get_settings(['volume_service'])

    def get_ec2_data(self):
        """Retrieve ec2 settings from remote application.

        :returns: ec2 settings
        :rtype: dict
        """
        return self.get_settings(['ec2_host'])

    def get_restart_trigger(self):
        """Retrieve restart trigger from remote application.

        :returns: restart trigger
        :rtype: dict
        """
        return self.get_settings(['restart_trigger'])
