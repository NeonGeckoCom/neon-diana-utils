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
import os
import shutil
import unittest
import yaml

from unittest.mock import patch
from os.path import join, dirname, isdir, isfile


class TestConfiguration(unittest.TestCase):
    def test_validate_output_file(self):
        from neon_diana_utils.configuration import validate_output_path
        valid_output_path = join(dirname(__file__), 'test_output')
        self.assertFalse(isdir(valid_output_path))
        self.assertTrue(validate_output_path(valid_output_path))
        self.assertTrue(validate_output_path(valid_output_path))
        self.assertFalse(validate_output_path(dirname(valid_output_path)))
        self.assertTrue(validate_output_path(join(valid_output_path,
                                                  'test.txt')))
        shutil.rmtree(valid_output_path)

    @patch("click.confirm")
    def test_make_keys_config(self, confirm):
        from neon_diana_utils.configuration import make_keys_config
        confirm.return_value = False
        test_output_file = join(dirname(__file__), "test_keys.yaml")
        # Test without file write
        config = make_keys_config(False, test_output_file)
        self.assertFalse(isfile(test_output_file))
        self.assertIsInstance(config, dict)
        self.assertIsInstance(config['keys'], dict)
        self.assertIsInstance(config['ChatGPT'], dict)

        # Test with file write
        config2 = make_keys_config(True, test_output_file)
        self.assertTrue(isfile(test_output_file))
        self.assertEqual(config, config2)
        with open(test_output_file, 'r') as f:
            from_disk = yaml.safe_load(f)
        self.assertEqual(from_disk, config2)

        os.remove(test_output_file)

    def test_generate_rmq_config(self):
        from neon_diana_utils.configuration import generate_rmq_config
        test_output_file = join(dirname(__file__), "test_rmq.json")
        # Test without write
        config = generate_rmq_config("test_admin1", "test_password1")
        self.assertFalse(isfile(test_output_file))
        self.assertIsInstance(config, dict)
        self.assertEqual(config['users'][0], {'name': 'neon_api_utils',
                                              'password': 'Klatchat2021',
                                              'tags': ['backend', 'user']})
        self.assertEqual(config['users'][-1], {'name': 'test_admin1',
                                               'password': 'test_password1',
                                               'tags': ['administrator']})
        self.assertEqual(set(config.keys()), {'users', 'vhosts', 'permissions'})
        for user in config['users']:
            self.assertEqual(set(user.keys()), {'name', 'password', 'tags'})
        for vhost in config['vhosts']:
            self.assertEqual(set(vhost.keys()), {'name'})
            self.assertTrue(vhost['name'].startswith('/'))
        for permission in config['permissions']:
            self.assertEqual(set(permission.keys()),
                             {'user', 'vhost', 'configure', 'write', 'read'})

        # Test with valid write
        config2 = generate_rmq_config("test_admin2", "test_password2",
                                      test_output_file)
        self.assertTrue(isfile(test_output_file))
        self.assertNotEqual(config, config2)
        self.assertEqual(config2['users'][-1], {'name': 'test_admin2',
                                                'password': 'test_password2',
                                                'tags': ['administrator']})
        with open(test_output_file, 'r') as f:
            from_disk = json.load(f)
        self.assertEqual(config2, from_disk)

        # Test invalid write
        config3 = generate_rmq_config("test_admin3", "test_password3",
                                      test_output_file)
        self.assertTrue(isfile(test_output_file))
        self.assertNotEqual(config2, config3)
        self.assertEqual(config3['users'][-1], {'name': 'test_admin3',
                                                'password': 'test_password3',
                                                'tags': ['administrator']})
        with open(test_output_file, 'r') as f:
            from_disk = json.load(f)
        self.assertEqual(config2, from_disk)

        os.remove(test_output_file)

    def test_generate_mq_auth_config(self):
        from neon_diana_utils.configuration import generate_mq_auth_config, \
            generate_rmq_config
        mq_config = generate_rmq_config("test", "test")
        auth = generate_mq_auth_config(mq_config)
        self.assertIsInstance(auth, dict)
        for service_auth in auth.values():
            rmq_users = [user for user in mq_config['users']
                         if user['name'] == service_auth['user']]
            self.assertEqual(len(rmq_users), 1)
            user = rmq_users[0]
            self.assertEqual(user['name'], service_auth['user'])
            self.assertEqual(user['password'], service_auth['password'])

    def test_configure_backend(self):
        from neon_diana_utils.configuration import configure_backend
        # TODO


class TestKubernetesUtils(unittest.TestCase):
    def test_generate_github_secret(self):
        from neon_diana_utils.kubernetes_utils import create_github_secret
        output_path = os.path.join(os.path.dirname(__file__), "test_gh.yaml")
        output_file = create_github_secret("username",
                                           "123123adsfasdf123123",
                                           output_path)
        self.assertTrue(os.path.isfile(output_file))
        self.assertEqual(output_file, output_path)
        with open(output_file) as f:
            contents = yaml.safe_load(f)
        self.assertEqual(contents['kind'], "Secret")
        self.assertEqual(contents['type'], "kubernetes.io/dockerconfigjson")
        self.assertEqual(contents['metadata']['name'], 'github-auth')
        self.assertEqual(contents['data']['.dockerconfigjson'],
                         "eyJhdXRocyI6IHsiZ2hjci5pbyI6IHsiYXV0aCI6ICJkWE5sY201"
                         "aGJXVTZNVEl6TVRJellXUnpabUZ6WkdZeE1qTXhNak09In19fQ=="
                         )

        with self.assertRaises(FileExistsError):
            create_github_secret("test", "test", output_path)

        os.remove(output_path)


class TestRabbitMQAPI(unittest.TestCase):
    from neon_diana_utils.rabbitmq_api import RabbitMQAPI
    # TODO


if __name__ == '__main__':
    unittest.main()
