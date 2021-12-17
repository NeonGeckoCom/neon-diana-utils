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

import docker

from os import getenv
from os.path import join, dirname, expanduser
from typing import Optional

from docker.errors import APIError
from docker.models.containers import Container
from ruamel.yaml import YAML
from neon_utils import LOG

from neon_diana_utils.utils import configure_diana_backend


def _run_clean_rabbit_mq_docker(bind_existing: bool = False) -> Container:
    """
    Start a clean RabbitMQ Docker instance to generate configuration files
    :param bind_existing: If true, allows for binding to a running container
        WARNING: setting `bind_existing` can result in overwriting valid MQ configuration
    """
    docker_client = docker.from_env()
    try:
        container = docker_client.containers.run("rabbitmq:3-management",
                                                 ports={"15672": "15672",
                                                        "5672": "5672"},
                                                 detach=True)
    except APIError as e:
        if e.status_code == 500:
            LOG.warning("Is an instance of RabbitMQ already running?")
            if bind_existing:
                for c in docker_client.containers.list():
                    if "rabbitmq:3-management" in c.image.tags:
                        LOG.info(f"Found a running RabbitMQ instance to configure")
                        return c
        else:
            LOG.error(e)
        raise e
    return container


def cleanup_docker_container(container_to_remove: Container):
    """
    Stop and remove the specified Docker Container
    :param container_to_remove: Docker.Container object to stop and remove
    """
    container_to_remove.stop()
    container_to_remove.remove()


def create_diana_docker_configurations(admin_user: str, admin_pass: str,
                                       services: set, config_path: str = None,
                                       allow_bind_existing: bool = False):
    """
    Create configuration files for Neon Diana.
    :param admin_user: username to configure for RabbitMQ configuration
    :param admin_pass: password associated with admin_user
    :param services: list of services to configure on this backend
    :param config_path: path to write configuration files (default=NEON_CONFIG_PATH)
    :param allow_bind_existing: bool to allow overwriting configuration for a running RabbitMQ instance
    """
    container = _run_clean_rabbit_mq_docker(allow_bind_existing)
    container_logs = container.logs(stream=True)
    for log in container_logs:
        if b"Server startup complete" in log:
            break
    configure_diana_backend("http://0.0.0.0:15672", admin_user, admin_pass, services, config_path)

    cleanup_docker_container(container)


def write_docker_compose(services_config: dict, compose_file: Optional[str] = None):
    """
    Generates and writes a docker-compose.yml according to the specified services
    :param services_config: dict services, usually read from service_mappings.yml
    :param compose_file: path of docker-compose.yml file to write
    """
    compose_file = compose_file if compose_file else \
        join(getenv("NEON_CONFIG_PATH", "~/.config/neon"), "docker-compose.yml")
    compose_file = expanduser(compose_file)

    with open(join(dirname(__file__), "templates", "docker-compose.yml")) as f:
        compose_boilerplate = YAML().load(f)
    compose_contents = {**compose_boilerplate, **{"services": services_config}}

    neon_config_path = dirname(compose_file)
    neon_metric_path = expanduser(getenv("NEON_METRIC_PATH", f"{neon_config_path}/metrics"))
    with open(compose_file, "w+") as f:
        YAML().dump(compose_contents, f)
        f.seek(0)
        string_contents = f.read()
        string_contents = string_contents.replace("${NEON_CONFIG_PATH}",
                                                  neon_config_path)\
            .replace("${NEON_METRIC_PATH}", neon_metric_path)
        f.seek(0)
        f.truncate(0)
        f.write(string_contents)
