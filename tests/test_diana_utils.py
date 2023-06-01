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
import yaml

from docker.errors import APIError
from mock import Mock

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from neon_diana_utils.constants import Orchestrator

MOCK_RMQ_USERS = {"users": [
    {"name": "neon_api_utils",
     "password": "Klatchat2021"},
    {"name": "neon_metrics",
     "password": "neon_metrics_password"},
    {"name": "neon_coupons",
     "password": "neon_coupons_password"},
    {"name": "neon_email",
     "password": "neon_email_password"},
    {"name": "neon_script_parser",
     "password": "neon_scripts_password"},
    {"name": "neon_api",
     "password": "neon_api_password"}
]}


class TestBackendUtils(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cached_config_path = os.environ.get("NEON_CONFIG_PATH")
        os.environ["NEON_CONFIG_PATH"] = os.path.join(os.path.dirname(__file__), "config")

    @classmethod
    def tearDownClass(cls) -> None:
        os.environ.pop("NEON_CONFIG_PATH")
        if cls.cached_config_path:
            os.environ["NEON_CONFIG_PATH"] = cls.cached_config_path

    def test_cli_configure_backend(self):
        from neon_diana_utils.constants import default_mq_services
        from neon_diana_utils.utils.backend import cli_configure_backend
        test_config_dir = os.path.join(os.path.dirname(__file__), "test_config")
        os.makedirs(test_config_dir, exist_ok=True)

        with self.assertRaises(ValueError):
            cli_configure_backend(None, default_mq_services(),
                                  "admin", "pass", True, "", "", True,
                                  "mq-backend",
                                  "http-backend")
        with self.assertRaises(FileExistsError):
            cli_configure_backend(__file__, default_mq_services(),
                                  "admin", "pass", True, "", "", True,
                                  "mq-backend",
                                  "http-backend")
        with self.assertRaises(ValueError):
            cli_configure_backend(test_config_dir, default_mq_services(),
                                  "admin", "", True, "", "", False,
                                  "mq-backend",
                                  "http-backend")

        with self.assertRaises(ValueError):
            cli_configure_backend(test_config_dir, set(),
                                  "admin", "pass", False, "", "", False,
                                  "mq-backend",
                                  "http-backend")

        cli_configure_backend(test_config_dir, default_mq_services(),
                              "", "", True, "", "", True,
                              "mq-backend",
                              "http-backend")
        docker_compose = os.path.join(test_config_dir, "docker-compose.yml")
        kubernetes_spec = os.path.join(test_config_dir, "services",
                                       "k8s_diana_backend.yml")
        kubernetes_ingress = os.path.join(test_config_dir, "ingress",
                                          "k8s_patch_nginx_service.yml")
        kubernetes_tcp = os.path.join(test_config_dir, "ingress",
                                      "k8s_config_tcp_services.yml")
        for output in {docker_compose, kubernetes_spec, kubernetes_ingress,
                       kubernetes_tcp}:
            self.assertTrue(os.path.isfile(output))
        shutil.rmtree(test_config_dir)

    def test_cli_start_backend(self):
        from neon_diana_utils.utils.backend import cli_start_backend
        test_dir = os.path.join(os.path.dirname(__file__), "test_diana_services_config")

        with self.assertRaises(ValueError):
            cli_start_backend("", False, Orchestrator.DOCKER)

        with self.assertRaises(ValueError):
            cli_start_backend(os.path.dirname(__file__), False, Orchestrator.DOCKER)

        with self.assertRaises(ValueError):
            cli_start_backend(test_dir, False, Orchestrator.OPENSHIFT)

    def test_cli_stop_backend(self):
        from neon_diana_utils.utils.backend import cli_stop_backend
        test_dir = os.path.join(os.path.dirname(__file__), "test_diana_services_config")

        with self.assertRaises(ValueError):
            cli_stop_backend("", Orchestrator.DOCKER)

        with self.assertRaises(ValueError):
            cli_stop_backend(os.path.dirname(__file__), Orchestrator.DOCKER)

        with self.assertRaises(ValueError):
            cli_stop_backend(test_dir, Orchestrator.OPENSHIFT)

    def test_write_neon_mq_config(self):
        from neon_diana_utils.utils.backend import write_neon_mq_config
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

    def test_write_rabbit_config(self):
        from neon_diana_utils.utils.backend import write_rabbit_config
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
        from neon_diana_utils.constants import valid_mq_services,\
            valid_http_services
        from neon_diana_utils.utils.backend import _parse_services
        minimal_valid_services = {"neon-rabbitmq", "neon-api-proxy"}
        mq_services = set(valid_mq_services())
        invalid_services = {"neon-invalid", "neon_invalid"}
        http_services = valid_http_services()
        all_services = mq_services.union(http_services)

        minimal = _parse_services(minimal_valid_services)
        all_mq = _parse_services(all_services)
        invalid = _parse_services(invalid_services)
        http = _parse_services(http_services, "http-backend")
        complete_http = _parse_services(all_services, "http-backend")
        complete_mq = _parse_services(all_services)

        self.assertIsInstance(minimal, dict)
        self.assertEqual(set(minimal.keys()), minimal_valid_services)
        for _, val in minimal.items():
            self.assertIsInstance(val, dict)

        self.assertIsInstance(all_mq, dict)
        self.assertEqual(all_mq, complete_mq)
        self.assertEqual(set(all_mq.keys()), mq_services)
        for _, val in all_mq.items():
            self.assertIsInstance(val, dict)

        self.assertIsInstance(invalid, dict)
        self.assertEqual(set(invalid.keys()), set())

        self.assertIsInstance(http, dict)
        self.assertEqual(http, complete_http)
        self.assertEqual(set(http.keys()), http_services)
        for _, val in http.items():
            self.assertIsInstance(val, dict)

    def test_parse_vhosts(self):
        from neon_diana_utils.utils.backend import _parse_vhosts
        with open(os.path.join(os.path.dirname(__file__), "config", "valid_services_to_configure.json")) as f:
            valid_services = json.load(f)
        vhosts = _parse_vhosts(valid_services)
        self.assertIsInstance(vhosts, set)
        self.assertTrue(all(v.startswith('/') for v in vhosts))

    def test_parse_configuration(self):
        from neon_diana_utils.utils.backend import _parse_configuration
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
        import neon_diana_utils.utils.backend
        docker_mock = Mock()
        kubernetes_mock = Mock()
        neon_diana_utils.utils.backend.write_docker_compose = docker_mock
        neon_diana_utils.utils.backend.write_kubernetes_spec = \
            kubernetes_mock
        test_config_dir = os.path.dirname(__file__)
        docker_config = {"docker": "test"}
        kubernetes_config = ["k8s_test"]
        namespace_config = {"MQ_NAMESPACE": "mq-ns",
                            "HTTP_NAMESPACE": "http-ns"}
        neon_diana_utils.utils.backend.generate_backend_config(
            docker_config, kubernetes_config,
            test_config_dir, namespaces=namespace_config)
        docker_mock.assert_called_once()
        docker_mock.assert_called_with(docker_config,
                                       os.path.join(test_config_dir,
                                                    "docker-compose.yml"),
                                       "none", None
                                       )
        kubernetes_mock.assert_called_once()
        kubernetes_mock.assert_called_with(kubernetes_config, test_config_dir,
                                           namespace_config)

    def test_configure_mq_backend(self):
        pass

    def test_generate_rmq_config(self):
        from neon_diana_utils.utils.backend import generate_rmq_config
        config = generate_rmq_config()
        self.assertIsInstance(config['users'], list)
        for user in config['users']:
            self.assertIsInstance(user['name'], str)
            self.assertIsInstance(user['password'], str)
            self.assertNotEqual(user['password'], '')
            self.assertIsInstance(user['tags'], list)
            if user['name'] == "neon_api_utils":
                self.assertEqual(user['password'], "Klatchat2021")
        for vhost in config['vhosts']:
            self.assertTrue(vhost['name'].startswith('/'))
        for perm in config['permissions']:
            self.assertIsInstance(perm['user'], str)
            self.assertIsInstance(perm['vhost'], str)
            self.assertIsInstance(perm['configure'], str)
            self.assertIsInstance(perm['write'], str)
            self.assertIsInstance(perm['read'], str)

    def test_generate_mq_auth_config(self):
        from neon_diana_utils.utils.backend import generate_mq_auth_config
        config = generate_mq_auth_config(MOCK_RMQ_USERS)
        self.assertIsNotNone(config)
        for key, value in config.items():
            self.assertEqual(set(value.keys()), {'user', 'password'})
            self.assertIsInstance(value['user'], str)
            self.assertIsInstance(value['password'], str)


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

    @unittest.skip
    def test_run_and_cleanup_rabbit_mq_docker(self):
        from neon_diana_utils.utils.docker_utils import \
            run_clean_rabbit_mq_docker, cleanup_docker_container
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
        from neon_diana_utils.utils.docker_utils import write_docker_compose
        with open(os.path.join(os.path.dirname(__file__), "config", "valid_docker-compose-services.json")) as f:
            sample_config = json.load(f)
        write_docker_compose(sample_config)

        docker_compose_file = os.path.join(os.environ["NEON_CONFIG_PATH"], "docker-compose.yml")
        self.assertTrue(os.path.isfile(docker_compose_file))
        with open(docker_compose_file) as f:
            docker_compose = yaml.safe_load(f)
        self.assertIn("version", docker_compose)
        self.assertEqual(docker_compose["services"], sample_config)
        os.remove(docker_compose_file)


class TestKubernetesUtils(unittest.TestCase):
    def test_cli_make_rmq_config_map(self):
        import neon_diana_utils.utils.kubernetes_utils
        mock = Mock()
        real_method = neon_diana_utils.utils.kubernetes_utils.generate_config_map
        neon_diana_utils.utils.kubernetes_utils.generate_config_map = mock
        input_path = os.path.join(os.path.dirname(__file__),
                                  "test_diana_services_config")
        output_path = os.path.dirname(__file__)
        out = neon_diana_utils.utils.kubernetes_utils.cli_make_rmq_config_map(
            input_path, output_path
        )

        self.assertEqual(os.path.join(output_path, "k8s_config_rabbitmq.yml"),
                         out)

        mock.assert_called_once()
        args = mock.call_args[0]
        self.assertEqual(args[0], "rabbitmq")
        self.assertIsInstance(args[1], dict)
        self.assertEqual(set(args[1].keys()), {"rabbitmq.conf",
                                               "rabbit_mq_config.json"})

        output_path = __file__
        out = neon_diana_utils.utils.kubernetes_utils.cli_make_rmq_config_map(
            input_path, output_path
        )
        self.assertEqual(output_path, out)

        with self.assertRaises(FileNotFoundError):
            neon_diana_utils.utils.kubernetes_utils.cli_make_rmq_config_map(
                os.path.join(output_path, "__invalid"), output_path
            )

        with self.assertRaises(ValueError):
            neon_diana_utils.utils.kubernetes_utils.cli_make_rmq_config_map(
                input_path, "/tmp/__unlikely_path"
            )

        neon_diana_utils.utils.kubernetes_utils.generate_config_map = \
            real_method

    def test_cli_make_api_secret(self):
        import neon_diana_utils.utils.kubernetes_utils
        mock = Mock()
        real_method = neon_diana_utils.utils.kubernetes_utils.generate_secret
        neon_diana_utils.utils.kubernetes_utils.generate_secret = mock
        input_path = os.path.join(os.path.dirname(__file__),
                                  "test_diana_services_config")
        output_path = os.path.dirname(__file__)
        out = neon_diana_utils.utils.kubernetes_utils.cli_make_api_secret(
            input_path, output_path
        )
        self.assertEqual(out, output_path)

        mock.assert_called_once()
        args = mock.call_args[0]
        self.assertEqual(args[0], "ngi-auth")
        self.assertIsInstance(args[1], dict)
        self.assertEqual(set(args[1].keys()), {"ngi_auth_vars.yml"})
        self.assertTrue(args[2].startswith(output_path))

        with self.assertRaises(FileNotFoundError):
            neon_diana_utils.utils.kubernetes_utils.cli_make_api_secret(
                os.path.join(output_path, "__invalid"), output_path
            )

        neon_diana_utils.utils.kubernetes_utils.generate_secret = real_method

    def test_write_kubernetes_spec(self):
        from neon_diana_utils.utils.kubernetes_utils import \
            write_kubernetes_spec
        namespaces = {"MQ_NAMESPACE": "mq_namespace",
                      "HTTP_NAMESPACE": "http_namespace"}
        with open(os.path.join(os.path.dirname(__file__), "config",
                               "valid_k8s_config.json")) as f:
            k8s_config = json.load(f)
        test_k8s_path = os.path.join(os.path.dirname(__file__), "outputs")
        os.makedirs(test_k8s_path, exist_ok=True)
        write_kubernetes_spec(k8s_config, test_k8s_path, namespaces)
        k8s_diana = os.path.join(test_k8s_path, "services",
                                 "k8s_diana_backend.yml")
        k8s_ingress = os.path.join(test_k8s_path, "ingress",
                                   "k8s_patch_nginx_service.yml")

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
            kubernetes_spec = yaml.safe_load(f)
        _validate_k8s_spec(kubernetes_spec)

        with open(k8s_ingress) as f:
            nginx_ingress = yaml.safe_load(f)
            f.seek(0)
            string_contents = f.read()
        self.assertIsInstance(nginx_ingress['spec']['ports'][0], dict)

        # Validate namespace substitution
        self.assertNotIn("${", string_contents)

        shutil.rmtree(test_k8s_path)

    def test_generate_config_map(self):
        from neon_diana_utils.utils.kubernetes_utils import generate_config_map
        output_path = os.path.join(os.path.dirname(__file__), "outputs")
        os.makedirs(output_path, exist_ok=True)
        config_name = "test-config-map"
        config_data = {"some_filename.test": "text file contents\n",
                       "some_other_file.bak": b"byte contents"}

        output_file = os.path.join(output_path, f"k8s_config_{config_name}.yml")
        generate_config_map(config_name, config_data, output_file)
        self.assertTrue(os.path.isfile(output_file))

        with open(output_file) as f:
            contents = yaml.safe_load(f)

        self.assertEqual(contents["metadata"]["name"], config_name)
        self.assertEqual(contents["data"], config_data)
        self.assertEqual(contents["kind"], "ConfigMap")

        shutil.rmtree(output_path)

    def test_generate_secret(self):
        from neon_diana_utils.utils.kubernetes_utils import generate_secret
        output_path = os.path.join(os.path.dirname(__file__), "outputs")
        os.makedirs(output_path, exist_ok=True)
        secret_name = "test-secret"
        config_data = {"some_secret.test": "secret\ntext file contents\n",
                       "some_other_secret.bak": b"secret byte contents"}

        output_file = os.path.join(output_path, f"k8s_secret_{secret_name}.yml")
        generate_secret(secret_name, config_data, output_file)
        self.assertTrue(os.path.isfile(output_file))

        with open(output_file) as f:
            contents = yaml.safe_load(f)

        self.assertEqual(contents["metadata"]["name"], secret_name)
        self.assertEqual(contents["stringData"], config_data)
        self.assertEqual(contents["kind"], "Secret")
        self.assertEqual(contents["type"], "Opaque")

        shutil.rmtree(output_path)

    def test_generate_github_auth(self):
        from neon_diana_utils.utils.kubernetes_utils import cli_make_github_secret
        output_path = os.path.join(os.path.dirname(__file__), "outputs")
        os.makedirs(output_path, exist_ok=True)
        output_file = cli_make_github_secret("username",
                                             "123123adsfasdf123123",
                                             output_path)
        self.assertTrue(os.path.isfile(output_file))
        with open(output_file) as f:
            contents = yaml.safe_load(f)
        self.assertEqual(contents['kind'], "Secret")
        self.assertEqual(contents['type'], "kubernetes.io/dockerconfigjson")
        self.assertEqual(contents['metadata']['name'], 'github-auth')
        self.assertEqual(contents['data']['.dockerconfigjson'],
                         "eyJhdXRocyI6IHsiZ2hjci5pbyI6IHsiYXV0aCI6ICJkWE5sY201"
                         "aGJXVTZNVEl6TVRJellXUnpabUZ6WkdZeE1qTXhNak09In19fQ=="
                         )
        shutil.rmtree(output_path)

    def test_update_tcp_config(self):
        from neon_diana_utils.utils.kubernetes_utils import _update_tcp_config
        output_path = os.path.join(os.path.dirname(__file__), "outputs")
        os.makedirs(output_path, exist_ok=True)

        output_file = os.path.join(output_path, "tcp_test.yml")

        out_file = _update_tcp_config({'80': 'default/test:80'}, output_file)
        self.assertTrue(os.path.isfile(out_file))
        with open(out_file) as f:
            config = yaml.safe_load(f)
        self.assertEqual(config['apiVersion'], 'v1')
        self.assertEqual(config['kind'], 'ConfigMap')
        self.assertEqual(config['metadata'], {'name': 'tcp-services',
                                              'namespace': 'ingress-nginx'})
        self.assertEqual(config['data'], {'80': 'default/test:80'})

        file = _update_tcp_config({'80': 'default/test:80'}, output_file)
        self.assertEqual(file, out_file)
        with open(file) as f:
            config_2 = yaml.safe_load(f)

        self.assertEqual(config, config_2)

        file = _update_tcp_config({'443': 'test/test:443'}, output_file)
        self.assertEqual(file, out_file)
        with open(file) as f:
            config = yaml.safe_load(f)
        self.assertEqual(config['data'], {'80': 'default/test:80',
                                          '443': 'test/test:443'})

        shutil.rmtree(output_path)

    def test_update_ingress_config(self):
        from neon_diana_utils.utils.kubernetes_utils import _update_ingress_config
        output_path = os.path.join(os.path.dirname(__file__), "outputs")
        os.makedirs(output_path, exist_ok=True)

        output_file = os.path.join(output_path, "ingress_test.yml")
        out_file = _update_ingress_config("test.neon.ai", "test_service", 80,
                                          output_path=output_file)
        self.assertTrue(os.path.isfile(out_file))
        with open(out_file) as f:
            config = yaml.safe_load(f)
        self.assertEqual(config['apiVersion'], 'networking.k8s.io/v1')
        self.assertEqual(config['kind'], "Ingress")
        self.assertIsInstance(
            config['metadata']['annotations']['cert-manager.io/issuer'], str)
        self.assertIn("test.neon.ai", config['spec']['tls'][0]['hosts'])
        self.assertTrue(any(x for x in config['spec']['rules'] if
                            x['host'] == "test.neon.ai" and
                            x['http']['paths'][0]['backend']['service']
                            ['name'] == "test_service" and
                            x['http']['paths'][0]['backend']['service']
                            ['port']['number'] == 80
                            ))

        with self.assertRaises(RuntimeError):
            _update_ingress_config("test.neon.ai", "test_service",
                                   80, "other-cert-issuer",
                                   output_path=output_file)

        out_file_2 = _update_ingress_config("test.neon.ai", "test_service", 80,
                                            output_path=output_file)
        self.assertEqual(out_file, out_file_2)
        with open(out_file_2) as f:
            config_2 = yaml.safe_load(f)
        self.assertEqual(config, config_2)

        out_file = _update_ingress_config("valid.neon.ai", "valid_service",
                                          8080, output_path=output_file)
        with open(out_file) as f:
            config = yaml.safe_load(f)

        self.assertIn("test.neon.ai", config['spec']['tls'][0]['hosts'])
        self.assertIn("valid.neon.ai", config['spec']['tls'][0]['hosts'])
        self.assertTrue(any(x for x in config['spec']['rules'] if
                            x['host'] == "test.neon.ai" and
                            x['http']['paths'][0]['backend']['service']
                            ['name'] == "test_service" and
                            x['http']['paths'][0]['backend']['service']
                            ['port']['number'] == 80
                            ))
        self.assertTrue(any(x for x in config['spec']['rules'] if
                            x['host'] == "valid.neon.ai" and
                            x['http']['paths'][0]['backend']['service']
                            ['name'] == "valid_service" and
                            x['http']['paths'][0]['backend']['service']
                            ['port']['number'] == 8080
                            ))

        shutil.rmtree(output_path)

    def test_create_cert_issuer(self):
        from neon_diana_utils.utils.kubernetes_utils import _create_cert_issuer
        output_path = os.path.join(os.path.dirname(__file__), "outputs")
        os.makedirs(output_path, exist_ok=True)

        output_file = os.path.join(output_path, "ingress_test.yml")
        file = _create_cert_issuer("letsencrypt-prod", "test@neon.ai",
                                   output_file)
        self.assertEqual(file, output_file)
        with open(file) as f:
            config = yaml.safe_load(f)

        self.assertEqual(config['kind'], 'Issuer')
        self.assertEqual(config['metadata']['name'], 'letsencrypt-prod')
        self.assertEqual(config['spec']['acme']['email'], "test@neon.ai")

        file = _create_cert_issuer("letsencrypt-test", "test1@neon.ai",
                                   output_file)
        self.assertEqual(file, output_file)
        with open(file) as f:
            config = yaml.safe_load(f)

        self.assertEqual(config['kind'], 'Issuer')
        self.assertEqual(config['metadata']['name'], 'letsencrypt-test')
        self.assertEqual(config['spec']['acme']['email'], "test1@neon.ai")

        shutil.rmtree(output_path)


if __name__ == '__main__':
    unittest.main()
