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
import unittest
import docker
import docker.models.containers

from docker.errors import APIError
from mock import Mock
from ruamel.yaml import YAML

from neon_diana_utils.utils import _run_clean_rabbit_mq, cleanup_docker_container, create_diana_configurations, \
    write_neon_mq_config, write_rabbit_config, write_docker_compose


class TestDianaUtils(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cached_config_path = os.environ.get("NEON_CONFIG_PATH")
        os.environ["NEON_CONFIG_PATH"] = os.path.join(os.path.dirname(__file__), "config")

    @classmethod
    def tearDownClass(cls) -> None:
        os.environ.pop("NEON_CONFIG_PATH")
        if cls.cached_config_path:
            os.environ["NEON_CONFIG_PATH"] = cls.cached_config_path

    def test_run_clean_rmq_docker(self):
        container = _run_clean_rabbit_mq()
        self.assertIsInstance(container, docker.models.containers.Container)
        self.assertIn(container, docker.from_env().containers.list())
        cleanup_docker_container(container)
        self.assertNotIn(container, docker.from_env().containers.list(all=True))

        _run_clean_rabbit_mq()
        with self.assertRaises(APIError):
            _run_clean_rabbit_mq()
        container = _run_clean_rabbit_mq(True)
        self.assertIsInstance(container, docker.models.containers.Container)
        self.assertIn(container, docker.from_env().containers.list())
        cleanup_docker_container(container)
        self.assertNotIn(container, docker.from_env().containers.list(all=True))

    def test_create_diana_configurations(self):
        create_diana_configurations("admin", "admin", {"neon_rabbitmq",
                                                       "neon_api_proxy",
                                                       "neon_metrics_service",
                                                       "neon_unknown"})
        valid_files = {"docker-compose.yml", "mq_config.json", "rabbitmq.conf", "rabbit_mq_config.json", ".env"}
        for file in valid_files:
            file_path = os.path.join(os.environ["NEON_CONFIG_PATH"], file)
            self.assertTrue(os.path.isfile(file_path))
            os.remove(file_path)

    def test_write_neon_mq_config(self):
        sample_creds = {
            'neon_metrics_connector':
                {'user': 'neon_metrics',
                 'password': 'jWAPqP4a2oL8mOq2T5Lj8cxMo72KwXv6keh1WItNWSk'},
            'neon_api_connector':
                {'user': 'neon_api',
                 'password': 'N3h-w4I561l20gZ_cSRvuMHdseYVYA-wHlw-6aJh0VQ'}}
        write_neon_mq_config(sample_creds)
        config_file = os.path.join(os.environ["NEON_CONFIG_PATH"], "mq_config.json")
        self.assertTrue(os.path.isfile(config_file))
        with open(config_file) as f:
            config = json.load(f)
        self.assertEqual(config["users"], sample_creds)
        self.assertIsInstance(config["server"], str)
        os.remove(config_file)

    def test_write_neon_rabbit_config(self):
        with open(os.path.join(os.path.dirname(__file__), "config", "valid_rabbitmq.json")) as f:
            sample_config = json.load(f)
        api = Mock()

        def get_definitions():
            return sample_config
        api.get_definitions = get_definitions

        write_rabbit_config(api)

        config_file = os.path.join(os.environ["NEON_CONFIG_PATH"], "rabbit_mq_config.json")
        self.assertTrue(os.path.isfile(config_file))
        with open(config_file) as f:
            config = json.load(f)
        self.assertEqual(config, sample_config)
        os.remove(config_file)

        rabbitmq_conf = os.path.join(os.environ["NEON_CONFIG_PATH"], "rabbitmq.conf")
        self.assertTrue(os.path.isfile(rabbitmq_conf))
        with open(rabbitmq_conf) as f:
            self.assertIn("load_definitions = /config/rabbit_mq_config.json", f.read())
        os.remove(rabbitmq_conf)

    def test_write_docker_compose(self):
        with open(os.path.join(os.path.dirname(__file__), "config", "valid_docker-compose.json")) as f:
            sample_config = json.load(f)
        write_docker_compose(sample_config)

        docker_compose_file = os.path.join(os.environ["NEON_CONFIG_PATH"], "docker-compose.yml")
        self.assertTrue(os.path.isfile(docker_compose_file))
        with open(docker_compose_file) as f:
            docker_compose = YAML().load(f)
        self.assertIn("version", docker_compose)
        self.assertEqual(docker_compose["services"], sample_config)
        os.remove(docker_compose_file)

        docker_env_file = os.path.join(os.environ["NEON_CONFIG_PATH"], ".env")
        with open(docker_env_file) as f:
            environ = f.read()
        self.assertIn(f"NEON_CONFIG_PATH={os.environ['NEON_CONFIG_PATH']}", environ)
        self.assertIn("NEON_METRIC_PATH=", environ)
        os.remove(docker_env_file)


if __name__ == '__main__':
    unittest.main()
