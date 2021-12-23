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
from neon_diana_utils.orchestrators import Orchestrator
from neon_diana_utils.utils.docker_utils import run_clean_rabbit_mq_docker, cleanup_docker_container, \
    write_docker_compose


def create_diana_configurations(admin_user: str, admin_pass: str,
                                services: set, config_path: str = None,
                                allow_bind_existing: bool = False,
                                volume_driver: str = "none",
                                volumes: Optional[dict] = None):
    """
    Create configuration files for Neon Diana.
    :param admin_user: username to configure for RabbitMQ configuration
    :param admin_pass: password associated with admin_user
    :param services: list of services to configure on this backend
    :param config_path: path to write configuration files (default=NEON_CONFIG_PATH)
    :param allow_bind_existing: bool to allow overwriting configuration for a running RabbitMQ instance
    :param volume_driver: Docker volume driver (https://docs.docker.com/storage/volumes/#use-a-volume-driver)
    :param volumes: Optional dict of volume names to directories (including hostnames for nfs volumes)
    """
    container = run_clean_rabbit_mq_docker(allow_bind_existing)
    container_logs = container.logs(stream=True)
    for log in container_logs:
        if b"Server startup complete" in log:
            break
    configure_diana_backend("http://0.0.0.0:15672", admin_user, admin_pass,
                            services, config_path, volume_driver, volumes)
    cleanup_docker_container(container)


def configure_diana_backend(url: str, admin_user: str, admin_pass: str,
                            services: set, config_path: str = None,
                            volume_driver: str = "none",
                            volumes: Optional[dict] = None):
    """
    Configure a new Diana RabbitMQ backend
    :param url: URL of admin portal (i.e. http://0.0.0.0:15672)
    :param admin_user: username to configure for RabbitMQ configuration
    :param admin_pass: password associated with admin_user
    :param services: list of services to configure on this backend
    :param config_path: local path to write configuration files (default=NEON_CONFIG_PATH)
    :param volume_driver: Docker volume driver (https://docs.docker.com/storage/volumes/#use-a-volume-driver)
    :param volumes: Optional dict of volume names to directories (including hostnames for nfs volumes)
    """
    api = RabbitMQAPI(url)

    # Configure Administrator
    api.login("guest", "guest")
    api.configure_admin_account(admin_user, admin_pass)

    # Read configuration from templates
    template_file = join(dirname(dirname(__file__)), "templates",
                         "service_mappings.yml")
    with open(template_file) as f:
        template_data = YAML().load(f)
    services_to_configure = {name: dict(template_data[name])
                             for name in services if name in template_data}

    # Warn for unknown requested services
    if set(services_to_configure.keys()) != set(services):
        unhandled_services = [s for s in services if s not in services_to_configure.keys()]
        LOG.warning(f"Some requested services not handled: {unhandled_services}")

    # Parse Configured Service Mapping
    vhosts_to_configure = set(itertools.chain.from_iterable([service.get("mq_vhosts", [])
                                                             for service in services_to_configure.values()]))
    users_to_configure = dict()
    neon_mq_user_auth = dict()
    docker_compose_configuration = dict()
    for name, service in services_to_configure.items():
        dict_merge(users_to_configure, service.get("mq_user_permissions", dict()))
        docker_compose_configuration[name] = service["docker_compose"]
        if service.get("mq_username"):
            # TODO: Update MQ services such that their service names match the docker container names DM
            neon_mq_user_auth[service.get("mq_service_name", name)] = {"user": service["mq_username"]}

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

    # Write out MQ config file
    for service in neon_mq_user_auth.values():
        service["password"] = credentials[service["user"]]
    neon_mq_config_file = join(expanduser(config_path), "mq_config.json") if config_path else None
    write_neon_mq_config(neon_mq_user_auth, neon_mq_config_file)

    # Generate docker-compose file
    docker_compose_file = join(expanduser(config_path), "docker-compose.yml") if config_path else None
    write_docker_compose(docker_compose_configuration, docker_compose_file,
                         volume_driver, volumes)


def write_neon_mq_config(credentials: dict, config_file: Optional[str] = None):
    """
    Takes the passed credentials and exports an MQ config file based on the
    """
    config_file = config_file if config_file else \
        join(getenv("NEON_CONFIG_PATH", "~/.config/neon"), "mq_config.json")
    config_file = expanduser(config_file)
    if not exists(dirname(config_file)):
        os.makedirs(dirname(config_file))

    configuration = {"server": "neon-rabbitmq",
                     "users": credentials}
    LOG.info(f"Writing Neon MQ configuration to {config_file}")
    with open(config_file, 'w+') as new_config:
        json.dump(configuration, new_config, indent=2)


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
    with open(join(config_path, "rabbitmq.conf"), 'w+') as rabbit:
        rabbit.write(f"load_definitions = /config/{config_basename}")
