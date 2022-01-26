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
import subprocess

from os import makedirs, getenv
from os.path import expanduser, isdir, join, dirname, basename, exists, isfile
from typing import Optional, Set
from neon_utils import LOG
from ruamel.yaml import YAML
from neon_utils.configuration_utils import dict_merge

from neon_diana_utils.constants import valid_http_services, Orchestrator
from neon_diana_utils.rabbitmq_api import RabbitMQAPI
from neon_diana_utils.utils.docker_utils import run_clean_rabbit_mq_docker, cleanup_docker_container, \
    write_docker_compose
from neon_diana_utils.utils.kubernetes_utils import write_kubernetes_spec, generate_secret, generate_config_map


def cli_configure_backend(config_path: str, mq_services: Set[str],
                          admin_user: str, admin_pass: str, http: bool,
                          volume_driver: str, volume_path: str,
                          skip_config: bool, mq_namespace: str,
                          http_namespace: str):
    """
    Handle `configure-backend` CLI Command.
    """
    if not config_path:
        raise ValueError("config_path not specified")
    # Get actual config path
    config_path = expanduser(config_path)
    if isfile(config_path):
        raise FileExistsError(f"Specified output path is a file")
    if not isdir(config_path):
        makedirs(config_path)

    # Validate requested password
    if not skip_config and not admin_pass:
        raise ValueError("Null password")

    # Validate services
    if not mq_services and not http:
        raise ValueError("No services specified")

    # Parse volume paths
    volumes = None
    if volume_path:
        volumes = {"config": join(volume_path, "config"),
                   "metrics": join(volume_path, "metrics")}

    # Parse Namespaces
    namespaces = {"MQ_NAMESPACE": mq_namespace,
                  "HTTP_NAMESPACE": http_namespace}

    # Parse user and orchestrator configuration
    mq_services_config = _parse_services(mq_services, "mq-backend")
    users_to_configure, neon_mq_user_auth, \
        mq_docker_compose_configuration, mq_kubernetes_configuration = \
        _parse_configuration(mq_services_config)
    if http:
        _, _, http_docker_configuration, http_kubernetes_configuration = \
            _parse_configuration(_parse_services(valid_http_services(), "http-backend"))
        docker_configuration = {**mq_docker_compose_configuration,
                                **http_docker_configuration}
        kubernetes_configuration = [*mq_kubernetes_configuration,
                                    *http_kubernetes_configuration]
    else:
        docker_configuration = mq_docker_compose_configuration
        kubernetes_configuration = mq_kubernetes_configuration

    if not skip_config:
        configure_mq_backend(admin_user=admin_user, admin_pass=admin_pass,
                             services=mq_services_config, users_config=users_to_configure,
                             neon_mq_user_auth=neon_mq_user_auth)

    generate_backend_config(docker_compose_config=docker_configuration,
                            kubernetes_config=kubernetes_configuration,
                            config_path=config_path,
                            volume_driver=volume_driver,
                            volumes=volumes,
                            namespaces=namespaces)


def cli_start_backend(config_path: str, attach: bool,
                      orchestrator: Orchestrator):
    """
    Start a backend specified at the passed config_path
    :param config_path: path to backend spec files
    :param attach: attach the calling thread to the command output
    :param orchestrator: orchestrator to use to start backend services
    """

    # TODO: Validate the requested file is for a backend
    if not config_path:
        raise ValueError("Null config_path")

    config_path = expanduser(config_path)
    if not isfile(join(config_path, "docker-compose.yml")):
        raise ValueError(f"docker-compose.yml not found in {config_path}")

    if orchestrator == Orchestrator.DOCKER:
        docker_compose_command = "docker-compose up"
        if not attach:
            docker_compose_command += " --detach"
            subprocess.Popen(["/bin/bash", "-c", f"cd {config_path} && {docker_compose_command}"]).communicate()
        else:
            subprocess.Popen(["/bin/bash", "-c", f"cd {config_path} && {docker_compose_command}"]).communicate()
    else:
        raise ValueError("The requested orchestrator is not currently supported")


def cli_stop_backend(config_path: str, orchestrator: Orchestrator):
    """
    Stop a backend specified at the passed config_path
    :param config_path: path to backend spec files
    :param orchestrator: orchestrator to use to start backend services
    """

    # TODO: Validate the requested file is for a backend
    config_path = expanduser(config_path)
    if not config_path:
        raise ValueError("Null config_path")
    if not isfile(join(config_path, "docker-compose.yml")):
        raise ValueError(f"docker-compose.yml not found in {config_path}")

    if orchestrator == Orchestrator.DOCKER:
        docker_compose_command = "docker-compose down"
        subprocess.Popen(["/bin/bash", "-c", f"cd {config_path} && {docker_compose_command}"]).communicate()
    else:
        raise ValueError("The requested orchestrator is not currently supported")


def write_neon_mq_config(credentials: dict, config_file: Optional[str] = None):
    """
    Takes the passed credentials and exports an MQ credential config file
    :param credentials: MQ User credentials
    :param config_file: `mq_config.json` file to write
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
    :param api: Configured RabbitMQAPI object
    :param config_file: Path to `rabbit_mq_config.json` file to write
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


def _parse_services(requested_services: set,
                    service_class: str = "mq-backend") -> dict:
    """
    Parse requested services and return a dict mapping of valid service names
    to configurations read from service_mappings.yml
    :param requested_services: set of service names requested to be configured
    :param service_class: string class of services to parse (http, mq)
    :returns: mapping of service name to parameters required for configuration
    """
    # Read configuration from templates
    template_file = join(dirname(dirname(__file__)), "templates",
                         "service_mappings.yml")
    with open(template_file) as f:
        template_data = YAML().load(f)
    services_to_configure = {name: dict(template_data[name])
                             for name in requested_services if
                             name in template_data and
                             template_data[name]["service_class"] ==
                             service_class}

    # Warn for unknown requested services
    if set(services_to_configure.keys()) != set(requested_services):
        unhandled_services = [s for s in requested_services
                              if s not in services_to_configure.keys()]
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


def configure_mq_backend(admin_user: str, admin_pass: str,
                         config_path: str = None,
                         run_rabbit_mq: bool = True,
                         allow_bind_existing: bool = False,
                         url: str = "http://0.0.0.0:15672",
                         services: dict = None,
                         users_config: dict = None,
                         neon_mq_user_auth: dict = None):
    """
    Configure a new Diana RabbitMQ backend
    :param url: URL of admin portal (default=http://0.0.0.0:15672)
    :param admin_user: username to configure for RabbitMQ configuration
    :param admin_pass: password associated with admin_user
    :param run_rabbit_mq: start RabbitMQ Docker container to configure
    :param allow_bind_existing: allow configuring an existing rabbitMQ server
    :param config_path: local path to write configuration files
           (default=NEON_CONFIG_PATH)
    :param services: dict of services to configure on this backend
    :param users_config: dict of user permissions to configure
    :param neon_mq_user_auth: dict of MQ service names to credentials
    """
    # Start container for local configuration
    if run_rabbit_mq:
        container = run_clean_rabbit_mq_docker(allow_bind_existing)
        container_logs = container.logs(stream=True)
        for log in container_logs:
            if b"Server startup complete" in log:
                break
    else:
        container = None

    api = RabbitMQAPI(url)

    # Configure Administrator
    api.login("guest", "guest")
    api.configure_admin_account(admin_user, admin_pass)

    # Configure vhosts
    vhosts_to_configure = _parse_vhosts(services)
    LOG.debug(f"vhosts={vhosts_to_configure}")
    for vhost in vhosts_to_configure:
        api.add_vhost(vhost)

    # Configure users
    LOG.debug(f"users={users_config}")
    credentials = api.create_default_users(list(users_config.keys()))
    api.add_user("neon_api_utils", "Klatchat2021")

    # Configure user permissions
    for user, vhost_config in users_config.items():
        for vhost, permissions in vhost_config.items():
            if not api.configure_vhost_user_permissions(vhost, user, **permissions):
                LOG.error(f"Error setting Permission! {user} {vhost}")
                raise

    # Export and save rabbitMQ Config
    rabbit_mq_config_file = join(expanduser(config_path), "rabbit_mq_config.json") if config_path else None
    write_rabbit_config(api, rabbit_mq_config_file)
    # TODO: Generate config map DM

    if container:
        cleanup_docker_container(container)

    # Write out MQ Connector config file
    for service in neon_mq_user_auth.values():
        service["password"] = credentials[service["user"]]
    neon_mq_config_file = join(expanduser(config_path), "mq_config.json") if config_path else None
    write_neon_mq_config(neon_mq_user_auth, neon_mq_config_file)

    # # Generate docker-compose file
    # docker_compose_file = join(expanduser(config_path), "docker-compose.yml") if config_path else None
    # write_docker_compose(docker_compose_configuration, docker_compose_file,
    #                      volume_driver, volumes)
    #
    # # Generate Kubernetes spec file
    # write_kubernetes_spec(kubernetes_configuration, config_path, namespace)


def generate_backend_config(docker_compose_config: dict,
                            kubernetes_config: list,
                            config_path: Optional[str] = None,
                            volume_driver: str = "none",
                            volumes: Optional[dict] = None,
                            namespaces: dict = None):
    """
    Generate orchestrator configuration for the specified services
    :param docker_compose_config: dict of Docker compose container specs
    :param kubernetes_config: list of Kubernetes Service/Deployment specs
    :param config_path: local path to write configuration files
           (default=NEON_CONFIG_PATH)
    :param volume_driver: Docker volume driver
           (https://docs.docker.com/storage/volumes/#use-a-volume-driver)
    :param volumes: Optional dict of volume names to directories
           (including hostnames for nfs volumes)
    :param namespaces: k8s namespaces to configure
    """
    # Generate docker-compose file
    docker_compose_file = join(expanduser(config_path), "docker-compose.yml") if config_path else None
    write_docker_compose(docker_compose_config, docker_compose_file,
                         volume_driver, volumes)

    # Generate Kubernetes spec file
    write_kubernetes_spec(kubernetes_config, config_path, namespaces)
