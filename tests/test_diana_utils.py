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
    def test_orchestrator(self):
        from neon_diana_utils.configuration import Orchestrator
        self.assertEqual(Orchestrator("kubernetes"), Orchestrator.KUBERNETES)
        self.assertEqual(Orchestrator("docker-compose"), Orchestrator.COMPOSE)
        with self.assertRaises(ValueError):
            Orchestrator("invalid")

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
    def test_make_llm_bot_config(self, confirm):
        from neon_diana_utils.configuration import make_llm_bot_config
        confirm.return_value = False
        self.assertEqual(make_llm_bot_config(), {"llm_bots": {}})

        confirm.return_value = True
        config = make_llm_bot_config()
        self.assertIsInstance(config['llm_bots'], dict)
        self.assertIsInstance(config['llm_bots']['chat_gpt'], list)
        for bot in config['llm_bots']['chat_gpt']:
            self.assertEqual(set(bot), {'name', 'description'})

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
        self.assertIsInstance(config['LLM_CHAT_GPT'], dict)
        self.assertIsInstance(config['FastChat'], dict)
        hana_config = config.pop("hana")

        # Test with file write
        config2 = make_keys_config(True, test_output_file)
        self.assertTrue(isfile(test_output_file))
        with open(test_output_file, 'r') as f:
            from_disk = yaml.safe_load(f)
        self.assertEqual(from_disk, config2)

        # Test default configuration values
        hana_config2 = config2.pop("hana")
        self.assertEqual(config, config2)
        self.assertEqual(hana_config2.keys(), hana_config.keys())
        self.assertNotEqual(hana_config2, hana_config)

        os.remove(test_output_file)

    def test_update_rmq_config(self):
        from neon_diana_utils.configuration import update_rmq_config
        test_file = join(dirname(__file__), "test_rabbitmq.json")
        update_rmq_config(test_file)
        self.assertTrue(isfile(test_file))
        self.assertTrue(isfile(f"{test_file}.old"))
        with open(test_file) as f:
            new_config = json.load(f)
        with open(f"{test_file}.old") as f:
            old_config = json.load(f)
        self.assertIsInstance(new_config, dict)
        self.assertIsInstance(old_config, dict)
        for user in old_config['users']:
            self.assertIn(user, new_config['users'])

        # Ensure no duplicated users
        for user in new_config['users']:
            self.assertEqual(len([u for u in new_config['users']
                                  if u['name'] == user['name']]), 1, user)
        os.remove(test_file)
        shutil.move(f"{test_file}.old", test_file)

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

        # Ensure no duplicate users
        for user in config['users']:
            self.assertEqual(len([u for u in config['users']
                                  if u['name'] == user['name']]), 1, user)

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

    @patch("neon_diana_utils.configuration.click.prompt")
    @patch("neon_diana_utils.configuration.click.confirm")
    def test_generate_hana_config(self, confirm, prompt):
        from neon_diana_utils.configuration import generate_hana_config

        # Test all confirmed
        confirm.return_value = True
        prompt.side_effect = ['neon', 'neon', 60, 6]
        hana_config = generate_hana_config()
        self.assertIsInstance(hana_config['hana'], dict)
        hana_config = hana_config['hana']
        self.assertTrue(hana_config['enable_email'])
        self.assertEqual(hana_config['node_username'], 'neon')
        self.assertEqual(hana_config['node_password'], 'neon')
        self.assertIsInstance(hana_config['access_token_secret'], str)
        self.assertIsInstance(hana_config['refresh_token_secret'], str)
        self.assertEqual(hana_config['requests_per_minute'], 60)
        self.assertEqual(hana_config['auth_requests_per_minute'], 6)

        # Test none confirmed
        confirm.return_value = False
        prompt.side_effect = [30, 3]
        hana_config = generate_hana_config()
        self.assertIsInstance(hana_config['hana'], dict)
        hana_config = hana_config['hana']
        self.assertFalse(hana_config['enable_email'])
        self.assertIsNone(hana_config['node_username'])
        self.assertIsNone(hana_config['node_password'])
        self.assertIsInstance(hana_config['access_token_secret'], str)
        self.assertIsInstance(hana_config['refresh_token_secret'], str)
        self.assertEqual(hana_config['requests_per_minute'], 30)
        self.assertEqual(hana_config['auth_requests_per_minute'], 3)

    def test_update_env_file(self):
        from neon_diana_utils.configuration import update_env_file
        test_file = join(dirname(__file__), "test.env")
        shutil.copyfile(test_file, f"{test_file}.bak")
        update_env_file(test_file)
        with open(test_file) as f:
            contents = f.read()
        self.assertEqual(contents, f"REL_PATH={dirname(__file__)}/test\n"
                                   f"ABS_PATH=/tmp/test")
        shutil.move(f"{test_file}.bak", test_file)

    @patch("neon_diana_utils.configuration.click.prompt")
    @patch("neon_diana_utils.configuration.click.confirm")
    def test_get_mq_service_user_config(self, confirm, prompt):
        from neon_diana_utils.configuration import _get_mq_service_user_config
        config_file = join(dirname(__file__), "test_rabbitmq.json")

        confirm.return_value = True
        prompt.return_value = "testing"

        # Test config from rmq config
        user = _get_mq_service_user_config(None, None, "test", config_file)
        self.assertEqual(set(user.keys()), {"user", "password"})
        self.assertEqual(user['user'], "neon_test")
        self.assertEqual(user['password'], "neon_test_password")

        # Test no config available get from stdin
        user = _get_mq_service_user_config("", "", "test2", config_file)
        self.assertEqual(user, {"user": "testing", "password": "testing"})

        # Test no config available get from args
        user = _get_mq_service_user_config("username", "password", "test2",
                                           config_file)
        self.assertEqual(user, {"user": "username", "password": "password"})

    @patch("neon_diana_utils.configuration.click.confirm")
    def test_get_chatbots_mq_config(self, confirm):
        from neon_diana_utils.configuration import _get_chatbots_mq_config
        rmq_config_path = join(dirname(__file__), "test_rabbitmq.json")

        # Test no import
        confirm.return_value = False
        config = _get_chatbots_mq_config(rmq_config_path)
        self.assertEqual(list(config), ["MQ"])
        for user in config["MQ"]['users']:
            self.assertIn(config["MQ"]['users'][user]["user"],
                          ("neon_bot_submind", "neon_bot_facilitator"))
            if config["MQ"]['users'][user]["user"] == "neon_bot_submind":
                self.assertEqual(config["MQ"]['users'][user]["password"], "")
            else:
                self.assertEqual(config["MQ"]['users'][user]["password"], "")

        confirm.return_value = True
        config = _get_chatbots_mq_config(rmq_config_path)
        self.assertEqual(list(config), ["MQ"])
        for user in config["MQ"]['users']:
            self.assertIn(config["MQ"]['users'][user]["user"],
                          ("neon_bot_submind", "neon_bot_facilitator"))
            if config["MQ"]['users'][user]["user"] == "neon_bot_submind":
                self.assertEqual(config["MQ"]['users'][user]["password"],
                                 "submind_password")
            else:
                self.assertEqual(config["MQ"]['users'][user]["password"],
                                 "facilitator_password")

    def test_get_unconfigured_backend_services(self):
        from neon_diana_utils.configuration import _get_unconfigured_mq_backend_services
        all_configured = {'keys': {'api_services': {'configured': True},
                                   'emails': {'configured': True},
                                   'track_my_brands': True},
                          'LLM_CHAT_GPT': {'config': False},
                          'LLM_CLAUDE': {'': ''},
                          'LLM_PALM2': 'enabled',
                          'LLM_GEMINI': 'enabled',
                          'LLM_FASTCHAT': True}
        disabled = _get_unconfigured_mq_backend_services(all_configured)
        self.assertEqual(disabled, set())

        none_configured = {'keys': {'api_services': {},
                                    'emails': None},
                           'LLM_CHAT_GPT': {}}
        disabled = _get_unconfigured_mq_backend_services(none_configured)
        self.assertEqual(disabled, {'neon-api-proxy', 'neon-brands-service',
                                    'neon-email-proxy', 'neon-llm-chatgpt',
                                    'neon-llm-fastchat', 'neon-llm-claude',
                                    'neon-llm-palm', 'neon-llm-gemini'})

    def test_get_optional_http_backend(self):
        from neon_diana_utils.configuration import _get_optional_http_backend
        self.assertGreater(len(_get_optional_http_backend()), 0)
        for service in _get_optional_http_backend():
            self.assertIsInstance(service, str)

        required_services = {'libretranslate', 'stt-nemo', 'tts-coqui'}
        for service in required_services:
            self.assertNotIn(service, _get_optional_http_backend(), service)

    def test_read_backend_domain(self):
        from neon_diana_utils.configuration import _read_backend_domain
        test_dir = join(dirname(__file__), "test_backend_domain")
        self.assertEqual(_read_backend_domain(test_dir), "test.tld")
        self.assertEqual(_read_backend_domain(join(test_dir, "diana-backend")),
                         "test.tld")
        with self.assertRaises(FileNotFoundError):
            _read_backend_domain(dirname(test_dir))

        # TODO: Test invalid values.yaml

    def test_configure_backend(self):
        from neon_diana_utils.configuration import configure_backend
        # TODO

    def test_configure_neon_core(self):
        from neon_diana_utils.configuration import configure_neon_core
        # TODO

    def test_configure_klat_chat(self):
        from neon_diana_utils.configuration import configure_klat_chat
        # TODO

    def test_configure_chatbots(self):
        from neon_diana_utils.configuration import configure_chatbots
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
