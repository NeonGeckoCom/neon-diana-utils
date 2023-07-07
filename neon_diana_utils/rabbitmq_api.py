# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2021 Neongecko.com Inc.
# BSD-3
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import json
import requests

from urllib.parse import quote_plus
from requests.auth import HTTPBasicAuth


class RabbitMQAPI:
    def __init__(self, url: str, verify_ssl: bool = False):
        """
        Creates an object used to interface with a RabbitMQ server
        :param url: Management URL (usually IP:port)
        """
        self._verify_ssl = verify_ssl
        self.console_url = url
        self._username = None
        self._password = None

    def login(self, username: str, password: str):
        """
        Sets internal username/password parameters used to generate HTTP auth
        :param username: user to authenticate as
        :param password: plaintext password to authenticate with
        """
        self._username = username
        self._password = password
        # TODO: Check auth and return DM

    @property
    def auth(self):
        """
        HTTPBasicAuth object to include with requests.
        """
        return HTTPBasicAuth(self._username, self._password)

    def add_vhost(self, vhost: str) -> bool:
        """
        Add a vhost to the server
        :param vhost: vhost to add
        :return: True if request was successful
        """
        status = requests.put(
            f"{self.console_url}/api/vhosts/{quote_plus(vhost)}",
            auth=self.auth, verify=self._verify_ssl)
        return status.ok

    def add_user(self, user: str, password: str, tags: str = "") -> bool:
        """
        Add a user to the server
        :param user: username to add
        :param password: password for user
        :param tags: comma-delimited list of tags to assign to new user
        :return: True if request was successful
        """
        tags = tags or ""
        body = {"password": password, "tags": tags}
        status = requests.put(
            f"{self.console_url}/api/users/{quote_plus(user)}",
            data=json.dumps(body), auth=self.auth, verify=self._verify_ssl)
        return status.ok

    def delete_user(self, user: str) -> bool:
        """
        Delete a user from the server
        :param user: username to remove
        """
        status = requests.delete(
            f"{self.console_url}/api/users/{quote_plus(user)}",
            auth=self.auth, verify=self._verify_ssl)
        return status.ok

    def configure_vhost_user_permissions(self, vhost: str, user: str,
                                         configure: str = ".*",
                                         write: str = ".*",
                                         read: str = ".*") -> bool:
        """
        Configure user's access to vhost. See RabbitMQ docs:
        https://www.rabbitmq.com/access-control.html#authorisation
        :param vhost: vhost to set/modify permissions for
        :param user: user to set/modify permissions of
        :param configure: regex configure permissions
        :param write: regex write permissions
        :param read: regex read permissions
        :return: True if request was successful
        """
        url = f"{self.console_url}/api/permissions/{quote_plus(vhost)}/" \
              f"{quote_plus(user)}"
        body = {"configure": configure,
                "write": write,
                "read": read}
        status = requests.put(url, data=json.dumps(body), auth=self.auth,
                              verify=self._verify_ssl)
        return status.ok

    def get_definitions(self):
        """
        Get the server definitions for RabbitMQ; these are used to persist
        configuration between container restarts
        """
        resp = requests.get(f"{self.console_url}/api/definitions",
                            auth=self.auth, verify=self._verify_ssl)
        data = json.loads(resp.content)
        return data

    def create_default_users(self, users: list) -> dict:
        """
        Creates the passed list of users with random passwords and returns a
        dict of users to passwords
        :param users: list of usernames to create
        :return: Dict of created usernames and associated passwords
        """
        import secrets
        credentials = dict()
        for user in users:
            passwd = secrets.token_urlsafe(32)
            credentials[user] = passwd
            self.add_user(user, passwd)
        return credentials

    def configure_admin_account(self, username: str, password: str) -> bool:
        """
        Configures an administrator with the passed credentials and removes
        the default account
        :param username: New administrator's username
        :param password: New administrator's password
        :return: True if action was successful
        """
        create = self.add_user(username, password, "administrator")
        self.login(username, password)
        delete = self.delete_user("guest")
        return create and delete
