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
import itertools

from os import getenv
from typing import Optional
from os.path import join, dirname, expanduser, basename, exists
from neon_utils import LOG
from ruamel.yaml import YAML
from neon_utils.configuration_utils import dict_merge

from neon_diana_utils.rabbitmq_api import RabbitMQAPI
from neon_diana_utils.utils.docker_utils import run_clean_rabbit_mq_docker, cleanup_docker_container, \
    write_docker_compose
from neon_diana_utils.utils.kompose_utils import write_kubernetes_spec, generate_secret, generate_config_map


def create_diana_configurations(admin_user: str, admin_pass: str,
                                services: set, config_path: str = None,
                                allow_bind_existing: bool = False,
                                volume_driver: str = "none",
                                volumes: Optional[dict] = None,
                                namespace: str = 'default'):
    """
    Create configuration files for Neon Diana.
    :param admin_user: username to configure for RabbitMQ configuration
    :param admin_pass: password associated with admin_user
    :param services: list of services to configure on this backend
    :param config_path: path to write configuration files (default=NEON_CONFIG_PATH)
    :param allow_bind_existing: bool to allow overwriting configuration for a running RabbitMQ instance
    :param volume_driver: Docker volume driver (https://docs.docker.com/storage/volumes/#use-a-volume-driver)
    :param volumes: Optional dict of volume names to directories (including hostnames for nfs volumes)
    :param namespace: k8s namespace to configure services to run in
    """
    container = run_clean_rabbit_mq_docker(allow_bind_existing)
    container_logs = container.logs(stream=True)
    for log in container_logs:
        if b"Server startup complete" in log:
            break
    configure_diana_backend("http://0.0.0.0:15672", admin_user, admin_pass,
                            services, config_path, volume_driver, volumes,
                            namespace)
    cleanup_docker_container(container)


def _parse_services(requested_services: set) -> dict:
    """
    Parse requested services and return a dict mapping of valid service names
    to configurations read from service_mappings.yml
    :param requested_services: set of service names requested to be configured
    :returns: mapping of service name to parameters required to configure the service
    """
    # Read configuration from templates
    template_file = join(dirname(dirname(__file__)), "templates",
                         "service_mappings.yml")
    with open(template_file) as f:
        template_data = YAML().load(f)
    services_to_configure = {name: dict(template_data[name])
                             for name in requested_services if name in template_data}

    # Warn for unknown requested services
    if set(services_to_configure.keys()) != set(requested_services):
        unhandled_services = [s for s in requested_services if s not in services_to_configure.keys()]
        LOG.warning(f"Some requested services not handled: {unhandled_services}")
    return services_to_configure


def _parse_vhosts(services_to_configure: dict) -> set:
    """
    Parse MQ vhosts specified in the requested configuration
    :param services_to_configure: service mapping parsed from service_mappings.yml
    :returns: set of vhosts to be created
    """
    return set(itertools.chain.from_iterable([service.get("mq", service).get("mq_vhosts", [])
                                              for service in services_to_configure.values()]))


def _parse_configuration(services_to_configure: dict) -> tuple:
    # Parse user and orchestrator configuration
    user_permissions = dict()
    neon_mq_auth = dict()
    docker_compose_configuration = dict()
    kubernetes_configuration = list()
    for name, service in services_to_configure.items():
        # Get service MQ Config
        if service.get("mq"):
            dict_merge(user_permissions, service.get("mq", service).get("mq_user_permissions", dict()))
            if service["mq"].get("mq_username"):
                # TODO: Update MQ services such that their service names match the container names DM
                neon_mq_auth[service.get("mq",
                                         service).get("mq_service_name", name)] = \
                    {"user": service.get("mq", service)["mq_username"]}
        docker_compose_configuration[name] = service["docker_compose"]
        kubernetes_configuration.extend(service.get("kubernetes") or list())
    return user_permissions, neon_mq_auth, docker_compose_configuration, kubernetes_configuration


def configure_diana_backend(url: str, admin_user: str, admin_pass: str,
                            services: set, config_path: str = None,
                            volume_driver: str = "none",
                            volumes: Optional[dict] = None,
                            namespace: str = 'default'):
    """
    Configure a new Diana RabbitMQ backend
    :param url: URL of admin portal (i.e. http://0.0.0.0:15672)
    :param admin_user: username to configure for RabbitMQ configuration
    :param admin_pass: password associated with admin_user
    :param services: list of services to configure on this backend
    :param config_path: local path to write configuration files (default=NEON_CONFIG_PATH)
    :param volume_driver: Docker volume driver (https://docs.docker.com/storage/volumes/#use-a-volume-driver)
    :param volumes: Optional dict of volume names to directories (including hostnames for nfs volumes)
    :param namespace: k8s namespace to configure services to run in
    """
    api = RabbitMQAPI(url)

    # Configure Administrator
    api.login("guest", "guest")
    api.configure_admin_account(admin_user, admin_pass)

    # Parse requested services
    services_to_configure = _parse_services(services)

    # Parse Configured Service Mapping
    vhosts_to_configure = _parse_vhosts(services_to_configure)

    # Parse user and orchestrator configuration
    users_to_configure, neon_mq_user_auth,\
        docker_compose_configuration, kubernetes_configuration = \
        _parse_configuration(services_to_configure)

    LOG.debug(f"vhosts={vhosts_to_configure}")
    LOG.debug(f"users={users_to_configure}")

    # Configure vhosts
    for vhost in vhosts_to_configure:
        api.add_vhost(vhost)

    # Configure users
    credentials = api.create_default_users(list(users_to_configure.keys()))
    api.add_user("neon_api_utils", "Klatchat2021")

    # Configure user permissions
    for user, vhost_config in users_to_configure.items():
        for vhost, permissions in vhost_config.items():
            if not api.configure_vhost_user_permissions(vhost, user, **permissions):
                LOG.error(f"Error setting Permission! {user} {vhost}")
                raise

    # Export and save rabbitMQ Config
    rabbit_mq_config_file = join(expanduser(config_path), "rabbit_mq_config.json") if config_path else None
    write_rabbit_config(api, rabbit_mq_config_file)
    # TODO: Generate config map DM

    # Write out MQ Connector config file
    for service in neon_mq_user_auth.values():
        service["password"] = credentials[service["user"]]
    neon_mq_config_file = join(expanduser(config_path), "mq_config.json") if config_path else None
    write_neon_mq_config(neon_mq_user_auth, neon_mq_config_file)

    # Generate docker-compose file
    docker_compose_file = join(expanduser(config_path), "docker-compose.yml") if config_path else None
    write_docker_compose(docker_compose_configuration, docker_compose_file,
                         volume_driver, volumes)

    # Generate Kubernetes spec file
    write_kubernetes_spec(kubernetes_configuration, config_path, namespace)


def generate_config(services: set, config_path: Optional[str] = None,
                    volume_driver: str = "none",  volumes: Optional[dict] = None,
                    namespace: str = 'default'):
    """
    Generate orchestrator configuration for the specified services
    :param services: list of services to configure on this backend
    :param config_path: local path to write configuration files (default=NEON_CONFIG_PATH)
    :param volume_driver: Docker volume driver (https://docs.docker.com/storage/volumes/#use-a-volume-driver)
    :param volumes: Optional dict of volume names to directories (including hostnames for nfs volumes)
    :param namespace: k8s namespace to configure
    """
    # Parse user and orchestrator configuration
    users_to_configure, neon_mq_user_auth, \
        docker_compose_configuration, kubernetes_configuration = \
        _parse_configuration(_parse_services(services))

    # Generate docker-compose file
    docker_compose_file = join(expanduser(config_path), "docker-compose.yml") if config_path else None
    write_docker_compose(docker_compose_configuration, docker_compose_file,
                         volume_driver, volumes)

    # Generate Kubernetes spec file
    write_kubernetes_spec(kubernetes_configuration, config_path, namespace)


def write_neon_mq_config(credentials: dict, config_file: Optional[str] = None):
    """
    Takes the passed credentials and exports an MQ config file based on the
    """
    config_file = config_file if config_file else \
        join(getenv("NEON_CONFIG_PATH", "~/.config/neon"), "mq_config.json")
    config_file = expanduser(config_file)
    config_path = dirname(config_file)
    if not exists(config_path):
        os.makedirs(config_path)

    configuration = {"server": "neon-rabbitmq",
                     "users": credentials}
    LOG.info(f"Writing Neon MQ configuration to {config_file}")
    with open(config_file, 'w+') as new_config:
        json.dump(configuration, new_config, indent=2)

    # Generate k8s secret
    generate_secret("mq-config", {"mq_config.json": json.dumps(configuration)},
                    join(config_path, "k8s_secret_mq-config.yml"))


def write_rabbit_config(api: RabbitMQAPI, config_file: Optional[str] = None):
    """
    Writes out RabbitMQ config files for persistence on next run
    """
    config_file = config_file if config_file else \
        join(getenv("NEON_CONFIG_PATH", "~/.config/neon"),
             "rabbit_mq_config.json")
    config_file = expanduser(config_file)
    config_path = dirname(config_file)
    if not exists(config_path):
        os.makedirs(config_path)

    config = api.get_definitions()
    LOG.info(f"Exporting Rabbit MQ configuration to {config_file}")
    with open(config_file, "w+") as exported:
        json.dump(config, exported, indent=2)

    config_basename = basename(config_file)
    rmq_conf_contents = f"load_definitions = /config/{config_basename}"
    with open(join(config_path, "rabbitmq.conf"), 'w+') as rabbit:
        rabbit.write(rmq_conf_contents)

    # Generate k8s config
    generate_config_map("rabbitmq", {"rabbit_mq_config.json": json.dumps(config),
                                     "rabbitmq.conf": rmq_conf_contents},
                        join(config_path, "k8s_config_rabbitmq.yml"))
