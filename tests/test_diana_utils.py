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
import sys
import unittest
import docker
import docker.models.containers

from docker.errors import APIError
from mock import Mock
from ruamel.yaml import YAML

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from neon_diana_utils.utils import create_diana_configurations, write_neon_mq_config, write_rabbit_config
from neon_diana_utils.utils.docker_utils import run_clean_rabbit_mq_docker,\
    cleanup_docker_container, write_docker_compose
from neon_diana_utils.utils.kompose_utils import generate_config_map, write_kubernetes_spec, generate_secret


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

    def test_create_diana_configurations(self):
        create_diana_configurations("admin", "admin", {"neon-rabbitmq",
                                                       "neon-api-proxy",
                                                       "neon-metrics-service",
                                                       "neon-unknown"})
        valid_files = {"docker-compose.yml", "mq_config.json", "rabbitmq.conf", "rabbit_mq_config.json"}
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

    def test_parse_services(self):
        from neon_diana_utils.cli import VALID_SERVICES
        from neon_diana_utils.utils import _parse_services
        minimal_valid_services = {"neon-rabbitmq", "neon-api-proxy"}
        all_valid_services = set(VALID_SERVICES)
        invalid_services = {"neon-invalid", "neon_invalid"}

        minimal = _parse_services(minimal_valid_services)
        complete = _parse_services(all_valid_services)
        invalid = _parse_services(invalid_services)

        self.assertIsInstance(minimal, dict)
        self.assertEqual(set(minimal.keys()), minimal_valid_services)
        for _, val in minimal.items():
            self.assertIsInstance(val, dict)

        self.assertIsInstance(complete, dict)
        self.assertEqual(set(complete.keys()), all_valid_services)
        for _, val in complete.items():
            self.assertIsInstance(val, dict)

        self.assertIsInstance(invalid, dict)
        self.assertEqual(set(invalid.keys()), set())

    def test_parse_vhosts(self):
        from neon_diana_utils.utils import _parse_vhosts
        with open(os.path.join(os.path.dirname(__file__), "config", "valid_services_to_configure.json")) as f:
            valid_services = json.load(f)
        vhosts = _parse_vhosts(valid_services)
        self.assertIsInstance(vhosts, set)
        self.assertTrue(all(v.startswith('/') for v in vhosts))

    def test_parse_configuration(self):
        from neon_diana_utils.utils import _parse_configuration
        with open(os.path.join(os.path.dirname(__file__), "config", "valid_services_to_configure.json")) as f:
            valid_services = json.load(f)

        mq_user_permissions, neon_mq_auth, docker_config, k8s_config = _parse_configuration(valid_services)

        self.assertIsInstance(mq_user_permissions, dict)
        for user, vhost_config in mq_user_permissions.items():
            self.assertIsInstance(user, str)
            self.assertIsInstance(vhost_config, dict)
            for route, perms in vhost_config.items():
                self.assertIsInstance(route, str)
                self.assertTrue(route.startswith('/'))
                self.assertEqual(set(perms.keys()), {"read", "write", "configure"})

        self.assertIsInstance(neon_mq_auth, dict)
        self.assertTrue(all([set(conf.keys()) == {"user"} for conf in neon_mq_auth.values()]))
        self.assertTrue(all([conf['user'] in mq_user_permissions for conf in neon_mq_auth.values()]))

        self.assertIsInstance(docker_config, dict)
        self.assertTrue(all([isinstance(conf, dict) for conf in docker_config.values()]))

        self.assertIsInstance(k8s_config, list)
        for config in k8s_config:
            self.assertIsInstance(config, dict)
            self.assertIsInstance(config["apiVersion"], str)
            self.assertIsInstance(config["kind"], str)
            self.assertIsInstance(config.get("metadata", dict()), dict)
            self.assertIsInstance(config["spec"], dict)

    def test_generate_config(self):
        pass


class TestDockerUtils(unittest.TestCase):
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
        container = run_clean_rabbit_mq_docker()
        self.assertIsInstance(container, docker.models.containers.Container)
        self.assertIn(container, docker.from_env().containers.list())
        cleanup_docker_container(container)
        self.assertNotIn(container, docker.from_env().containers.list(all=True))

        run_clean_rabbit_mq_docker()
        with self.assertRaises(APIError):
            run_clean_rabbit_mq_docker()
        container = run_clean_rabbit_mq_docker(True)
        self.assertIsInstance(container, docker.models.containers.Container)
        self.assertIn(container, docker.from_env().containers.list())
        cleanup_docker_container(container)
        self.assertNotIn(container, docker.from_env().containers.list(all=True))

    def test_write_docker_compose(self):
        with open(os.path.join(os.path.dirname(__file__), "config", "valid_docker-compose-services.json")) as f:
            sample_config = json.load(f)
        write_docker_compose(sample_config)

        docker_compose_file = os.path.join(os.environ["NEON_CONFIG_PATH"], "docker-compose.yml")
        self.assertTrue(os.path.isfile(docker_compose_file))
        with open(docker_compose_file) as f:
            docker_compose = YAML().load(f)
        self.assertIn("version", docker_compose)
        self.assertEqual(docker_compose["services"], sample_config)
        os.remove(docker_compose_file)


class TestKubernetesUtils(unittest.TestCase):
    def test_write_kubernetes_spec(self):
        namespace = "test"
        with open(os.path.join(os.path.dirname(__file__), "config", "valid_k8s_config.json")) as f:
            k8s_config = json.load(f)
        test_k8s_path = os.path.join(os.path.dirname(__file__), "outputs")
        os.makedirs(test_k8s_path)
        write_kubernetes_spec(k8s_config, test_k8s_path, namespace)
        k8s_diana = os.path.join(test_k8s_path, "k8s_diana.yml")
        k8s_ingress = os.path.join(test_k8s_path, "k8s_ingress_nginx_mq.yml")

        def _validate_k8s_spec(spec: dict):
            self.assertIn("apiVersion", spec)
            self.assertIn("kind", spec)
            self.assertIn("metadata", spec)
            self.assertIsInstance(spec["items"], list)
            for item in spec["items"]:
                self.assertIsInstance(item["kind"], str)
                self.assertIsInstance(item["apiVersion"], str)
                self.assertIsInstance(item["metadata"], dict)
                self.assertIsInstance(item.get("spec", dict()), dict)

        self.assertTrue(os.path.isfile(k8s_diana))
        with open(k8s_diana) as f:
            kubernetes_spec = YAML().load(f)
        _validate_k8s_spec(kubernetes_spec)

        with open(k8s_ingress) as f:
            nginx_ingress = YAML().load(f)
            f.seek(0)
            string_contents = f.read()
        _validate_k8s_spec(nginx_ingress)

        # Validate MQ_NAMESPACE substitution
        self.assertNotIn("${", string_contents)
        self.assertIn(namespace, string_contents)

        shutil.rmtree(test_k8s_path)

    def test_generate_config_map(self):
        output_path = os.path.join(os.path.dirname(__file__), "outputs")
        os.makedirs(output_path)
        config_name = "test-config-map"
        config_data = {"some_filename.test": "text file contents\n",
                       "some_other_file.bak": b"byte contents"}

        output_file = os.path.join(output_path, f"k8s_config_{config_name}.yml")
        generate_config_map(config_name, config_data, output_file)
        self.assertTrue(os.path.isfile(output_file))

        with open(output_file) as f:
            contents = YAML().load(f)

        self.assertEqual(contents["metadata"]["name"], config_name)
        self.assertEqual(contents["data"], config_data)
        self.assertEqual(contents["kind"], "ConfigMap")

        shutil.rmtree(output_path)

    def test_generate_secret(self):
        output_path = os.path.join(os.path.dirname(__file__), "outputs")
        os.makedirs(output_path)
        secret_name = "test-secret"
        config_data = {"some_secret.test": "secret\ntext file contents\n",
                       "some_other_secret.bak": b"secret byte contents"}

        output_file = os.path.join(output_path, f"k8s_secret_{secret_name}.yml")
        generate_secret(secret_name, config_data, output_file)
        self.assertTrue(os.path.isfile(output_file))

        with open(output_file) as f:
            contents = YAML().load(f)

        self.assertEqual(contents["metadata"]["name"], secret_name)
        self.assertEqual(contents["stringData"], config_data)
        self.assertEqual(contents["kind"], "Secret")
        self.assertEqual(contents["type"], "Opaque")

        shutil.rmtree(output_path)

    def test_convert_docker_compose(self):
        pass


if __name__ == '__main__':
    unittest.main()
